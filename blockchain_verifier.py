import os
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

import httpx


SOLANA_RPC_URL = os.getenv(
    "SOLANA_RPC_URL",
    "https://api.mainnet-beta.solana.com",
)

EVM_RPC_URLS = {
    "Ethereum": "https://ethereum-rpc.publicnode.com",
    "Robinhood": "https://rpc.mainnet.chain.robinhood.com",
    "BNB Chain": "https://bsc-rpc.publicnode.com",
    "Polygon": "https://polygon-bor-rpc.publicnode.com",
    "Arbitrum": "https://arbitrum-one-rpc.publicnode.com",
    "Avalanche": "https://avalanche-c-chain-rpc.publicnode.com",
    "Fantom": "https://fantom-rpc.publicnode.com",
    "Base": "https://base-rpc.publicnode.com",
    "Cronos": "https://evm.cronos.org",
    "Kava": "https://evm.kava.io",
}

SOLANA_SIGNATURE_PATTERN = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,90}$")
EVM_HASH_PATTERN = re.compile(r"^0x[0-9a-fA-F]{64}$")
EVM_ADDRESS_PATTERN = re.compile(r"^0x[0-9a-fA-F]{40}$")


@dataclass
class VerificationResult:
    status: str
    reason: str = ""


def normalize_transaction_hash(blockchain, transaction_hash):
    value = (transaction_hash or "").strip()
    if blockchain in EVM_RPC_URLS:
        return value.lower()
    return value


def parse_native_amount(amount_text, expected_currency):
    parts = (amount_text or "").strip().split()
    if len(parts) != 2 or parts[1] != expected_currency:
        return None
    try:
        amount = Decimal(parts[0])
    except InvalidOperation:
        return None
    if amount <= 0:
        return None
    return amount


async def _rpc(client, url, method, params):
    response = await client.post(
        url,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        },
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("error"):
        raise RuntimeError(payload["error"].get("message", "RPC request failed"))
    return payload.get("result")


async def _verify_solana(payment, transaction_hash):
    if not SOLANA_SIGNATURE_PATTERN.fullmatch(transaction_hash):
        return VerificationResult("rejected", "The Solana transaction signature is invalid.")

    expected_amount = payment["expected_amount"]
    recipient = payment["recipient_address"]
    if expected_amount is None:
        return VerificationResult(
            "unsupported",
            "The selected service does not have a native SOL amount configured.",
        )

    expected_lamports = int(Decimal(expected_amount) * Decimal(1_000_000_000))

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            status_result = await _rpc(
                client,
                SOLANA_RPC_URL,
                "getSignatureStatuses",
                [[transaction_hash], {"searchTransactionHistory": True}],
            )
            signature_statuses = status_result or []
            signature_status = signature_statuses[0] if signature_statuses else None
            if signature_status is None:
                return VerificationResult("pending", "Transaction is not visible yet.")
            if signature_status.get("err") is not None:
                return VerificationResult("rejected", "The transaction failed on-chain.")
            if signature_status.get("confirmationStatus") not in (
                "confirmed",
                "finalized",
            ):
                return VerificationResult("pending", "Transaction is still confirming.")

            transaction = await _rpc(
                client,
                SOLANA_RPC_URL,
                "getTransaction",
                [
                    transaction_hash,
                    {
                        "encoding": "jsonParsed",
                        "commitment": "confirmed",
                        "maxSupportedTransactionVersion": 0,
                    },
                ],
            )
    except (httpx.HTTPError, ValueError, RuntimeError) as error:
        return VerificationResult("pending", f"Blockchain lookup is temporarily unavailable: {error}")

    if not transaction:
        return VerificationResult("pending", "Transaction details are not available yet.")

    meta = transaction.get("meta") or {}
    if meta.get("err") is not None:
        return VerificationResult("rejected", "The transaction failed on-chain.")

    message = ((transaction.get("transaction") or {}).get("message") or {})
    account_keys = message.get("accountKeys") or []
    recipient_index = None
    for index, account in enumerate(account_keys):
        pubkey = account.get("pubkey") if isinstance(account, dict) else account
        if pubkey == recipient:
            recipient_index = index
            break

    pre_balances = meta.get("preBalances") or []
    post_balances = meta.get("postBalances") or []
    if (
        recipient_index is None
        or recipient_index >= len(pre_balances)
        or recipient_index >= len(post_balances)
    ):
        return VerificationResult(
            "rejected",
            "The transaction did not include the assigned receiving wallet.",
        )

    received_lamports = post_balances[recipient_index] - pre_balances[recipient_index]
    if received_lamports != expected_lamports:
        return VerificationResult(
            "rejected",
            "The received SOL amount does not match the required payment.",
        )

    return VerificationResult("confirmed")


def _hex_int(value):
    if value is None:
        return None
    try:
        return int(value, 16)
    except (TypeError, ValueError):
        return None


async def _verify_evm(payment, transaction_hash):
    rpc_url = EVM_RPC_URLS.get(payment["blockchain"])
    if rpc_url is None:
        return VerificationResult(
            "unsupported",
            "Automatic verification is not configured for this blockchain yet.",
        )
    if not EVM_HASH_PATTERN.fullmatch(transaction_hash):
        return VerificationResult("rejected", "The transaction hash is invalid.")
    if not EVM_ADDRESS_PATTERN.fullmatch(payment["recipient_address"]):
        return VerificationResult("rejected", "The receiving wallet address is invalid.")
    expected_amount = payment["expected_amount"]
    if expected_amount is None:
        return VerificationResult(
            "unsupported",
            "The selected service does not have a native coin amount configured.",
        )
    expected_wei = int(Decimal(expected_amount) * Decimal(10**18))
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            receipt = await _rpc(
                client,
                rpc_url,
                "eth_getTransactionReceipt",
                [transaction_hash],
            )
            if receipt is None:
                return VerificationResult("pending", "Transaction is not mined yet.")

            if receipt.get("status") != "0x1":
                return VerificationResult("rejected", "The transaction failed on-chain.")

            transaction = await _rpc(
                client,
                rpc_url,
                "eth_getTransactionByHash",
                [transaction_hash],
            )
            latest_block = await _rpc(client, rpc_url, "eth_blockNumber", [])
    except (httpx.HTTPError, ValueError, RuntimeError) as error:
        return VerificationResult("pending", f"Blockchain lookup is temporarily unavailable: {error}")

    if not transaction:
        return VerificationResult("pending", "Transaction details are not available yet.")
    transaction_recipient = transaction.get("to")
    if (
        not transaction_recipient
        or transaction_recipient.lower() != payment["recipient_address"].lower()
    ):
        return VerificationResult(
            "rejected",
            "The transaction was not sent to the assigned receiving wallet.",
        )

    if _hex_int(transaction.get("value")) != expected_wei:
        return VerificationResult(
            "rejected",
            "The received amount does not match the required payment.",
        )

    block_number = _hex_int(receipt.get("blockNumber"))
    current_block = _hex_int(latest_block)
    if (
        block_number is None
        or current_block is None
        or current_block - block_number < 1
    ):
        return VerificationResult("pending", "Transaction confirmation is not available yet.")

    return VerificationResult("confirmed")


async def verify_payment(payment, transaction_hash):
    if payment["blockchain"] == "Solana":
        return await _verify_solana(payment, transaction_hash)
    if payment["blockchain"] in EVM_RPC_URLS:
        return await _verify_evm(payment, transaction_hash)
    return VerificationResult(
        "unsupported",
        "Automatic verification is not configured for this blockchain yet.",
    )