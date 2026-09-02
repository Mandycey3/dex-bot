"""Resolve token identity and branding without relying on one indexer."""

import asyncio
import logging
import re
from typing import Any
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

GECKOTERMINAL_NETWORKS = {
    "Ethereum": "eth",
    "Robinhood": "robinhood",
    "BNB Chain": "bsc",
    "Polygon": "polygon_pos",
    "Arbitrum": "arbitrum",
    "Avalanche": "avax",
    "Fantom": "ftm",
    "Solana": "solana",
    "Base": "base",
    "Cronos": "cronos",
    "Kava": "kava",
    "TRON": "tron",
    "TON": "ton",
    "SUI": "sui-network",
}

COINGECKO_PLATFORMS = {
    "Ethereum": "ethereum",
    "Robinhood": "robinhood-chain",
    "BNB Chain": "binance-smart-chain",
    "Polygon": "polygon-pos",
    "Arbitrum": "arbitrum-one",
    "Avalanche": "avalanche",
    "Fantom": "fantom",
    "Solana": "solana",
    "Base": "base",
    "Cronos": "cronos",
    "Kava": "kava",
    "TRON": "tron",
    "TON": "the-open-network",
    "SUI": "sui",
}

TRUST_WALLET_CHAINS = {
    "Ethereum": "ethereum",
    "Robinhood": "robinhood",
    "BNB Chain": "smartchain",
    "Polygon": "polygon",
    "Arbitrum": "arbitrum",
    "Avalanche": "avalanchec",
    "Fantom": "fantom",
    "Solana": "solana",
    "Base": "base",
    "Cronos": "cronos",
    "Kava": "kava",
    "TRON": "tron",
    "TON": "ton",
    "SUI": "sui",
}

EVM_ADDRESS_PATTERN = re.compile(r"^0x[0-9a-fA-F]{40}$")
SOLANA_ADDRESS_PATTERN = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
EVM_RPC_METADATA = {
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


def _metadata(
    name: str | None,
    symbol: str | None = None,
    image_url: str | None = None,
    source: str | None = None,
    **extra: str | None,
) -> dict[str, str | None]:
    """Create a normalized metadata record and discard empty values."""
    values: dict[str, str | None] = {
        "name": name.strip() if isinstance(name, str) and name.strip() else None,
        "symbol": (
            symbol.strip()
            if isinstance(symbol, str) and symbol.strip()
            else None
        ),
        "image_url": image_url.strip()
        if isinstance(image_url, str) and image_url.strip()
        else None,
        "source": source,
    }
    values.update(extra)
    return {key: value for key, value in values.items() if value}


def _decode_abi_string(result: str | None) -> str | None:
    """Decode both dynamic ABI strings and bytes32 token metadata responses."""
    if not isinstance(result, str) or not result.startswith("0x"):
        return None
    try:
        payload = bytes.fromhex(result[2:])
    except ValueError:
        return None
    if not payload:
        return None

    # Standard ABI encoding: offset, byte length, UTF-8 bytes.
    if len(payload) >= 64:
        offset = int.from_bytes(payload[:32], "big")
        if offset + 32 <= len(payload):
            length = int.from_bytes(payload[offset : offset + 32], "big")
            start = offset + 32
            end = start + length
            if end <= len(payload):
                decoded = payload[start:end].rstrip(b"\x00").decode(
                    "utf-8", errors="ignore"
                )
                if decoded.strip():
                    return decoded.strip()

    # Older ERC-20 contracts sometimes return bytes32 directly.
    decoded = payload[:32].rstrip(b"\x00").decode("utf-8", errors="ignore")
    return decoded.strip() or None


async def _get_json(
    client: httpx.AsyncClient,
    url: str,
    *,
    source: str,
) -> dict[str, Any] | list[Any] | None:
    try:
        response = await client.get(url)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, (dict, list)):
            return payload
    except (httpx.HTTPError, ValueError) as error:
        logger.info("%s metadata lookup unavailable: %s", source, error)
    return None


async def _lookup_geckoterminal(
    client: httpx.AsyncClient,
    contract_address: str,
    blockchain: str,
) -> dict[str, str | None] | None:
    network = GECKOTERMINAL_NETWORKS.get(blockchain)
    if not network:
        return None
    url = (
        f"https://api.geckoterminal.com/api/v2/networks/{network}/tokens/"
        f"{quote(contract_address, safe='')}"
    )
    payload = await _get_json(client, url, source="GeckoTerminal")
    attributes = (
        payload.get("data", {}).get("attributes", {})
        if isinstance(payload, dict)
        else {}
    )
    if not isinstance(attributes, dict):
        return None
    return _metadata(
        attributes.get("name"),
        attributes.get("symbol"),
        attributes.get("image_url"),
        "GeckoTerminal",
        coingecko_coin_id=attributes.get("coingecko_coin_id"),
        price_usd=attributes.get("price_usd"),
        volume_24h=(attributes.get("volume_usd") or {}).get("h24")
        if isinstance(attributes.get("volume_usd"), dict)
        else None,
    ) or None


async def _lookup_coingecko(
    client: httpx.AsyncClient,
    contract_address: str,
    blockchain: str,
) -> dict[str, str | None] | None:
    platform = COINGECKO_PLATFORMS.get(blockchain)
    if not platform:
        return None
    url = (
        f"https://api.coingecko.com/api/v3/coins/{platform}/contract/"
        f"{quote(contract_address, safe='')}"
    )
    payload = await _get_json(client, url, source="CoinGecko")
    if not isinstance(payload, dict):
        return None
    image = payload.get("image") or {}
    image_url = (
        image.get("large") or image.get("small")
        if isinstance(image, dict)
        else None
    )
    return _metadata(
        payload.get("name"),
        payload.get("symbol"),
        image_url,
        "CoinGecko",
        price_usd=(payload.get("market_data") or {})
        .get("current_price", {})
        .get("usd")
        if isinstance(payload.get("market_data"), dict)
        else None,
        volume_24h=(payload.get("market_data") or {})
        .get("total_volume", {})
        .get("usd")
        if isinstance(payload.get("market_data"), dict)
        else None,
    ) or None


async def _lookup_jupiter(
    client: httpx.AsyncClient,
    contract_address: str,
    blockchain: str,
) -> dict[str, str | None] | None:
    if blockchain != "Solana" or not SOLANA_ADDRESS_PATTERN.fullmatch(contract_address):
        return None
    url = (
        "https://lite-api.jup.ag/tokens/v2/search?query="
        f"{quote(contract_address, safe='')}"
    )
    payload = await _get_json(client, url, source="Jupiter")
    if not isinstance(payload, list):
        return None
    requested = contract_address.lower()
    for token in payload:
        if not isinstance(token, dict):
            continue
        token_id = str(token.get("id") or token.get("address") or "")
        if token_id.lower() == requested:
            return _metadata(
                token.get("name"),
                token.get("symbol"),
                token.get("icon"),
                "Jupiter",
            ) or None
    return None


async def _lookup_pumpfun(
    client: httpx.AsyncClient,
    contract_address: str,
    blockchain: str,
) -> dict[str, str | None] | None:
    if blockchain != "Solana" or not SOLANA_ADDRESS_PATTERN.fullmatch(contract_address):
        return None
    url = (
        "https://frontend-api-v3.pump.fun/coins/"
        f"{quote(contract_address, safe='')}"
    )
    payload = await _get_json(client, url, source="Pump.fun")
    if not isinstance(payload, dict) or not payload.get("name"):
        return None
    return _metadata(
        payload.get("name"),
        payload.get("symbol"),
        payload.get("image_uri"),
        "Pump.fun",
        market_cap_usd=payload.get("usd_market_cap")
        or payload.get("market_cap_usd"),
        creator=payload.get("creator"),
        website=payload.get("website"),
        twitter=payload.get("twitter"),
    ) or None


async def _evm_call(
    client: httpx.AsyncClient,
    rpc_url: str,
    contract_address: str,
    selector: str,
) -> str | None:
    try:
        response = await client.post(
            rpc_url,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_call",
                "params": [{"to": contract_address, "data": selector}, "latest"],
            },
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("result") if isinstance(payload, dict) else None
    except (httpx.HTTPError, ValueError):
        return None


async def _lookup_evm_onchain(
    client: httpx.AsyncClient,
    contract_address: str,
    blockchain: str,
) -> dict[str, str | None] | None:
    rpc_url = EVM_RPC_METADATA.get(blockchain)
    if not rpc_url or not EVM_ADDRESS_PATTERN.fullmatch(contract_address):
        return None

    name_result, symbol_result = await asyncio.gather(
        _evm_call(client, rpc_url, contract_address, "0x06fdde03"),
        _evm_call(client, rpc_url, contract_address, "0x95d89b41"),
    )
    name = _decode_abi_string(name_result)
    symbol = _decode_abi_string(symbol_result)
    if not name and not symbol:
        return None
    return _metadata(name or symbol, symbol, source="On-chain ERC-20 metadata") or None


async def _lookup_dexscreener(
    client: httpx.AsyncClient,
    contract_address: str,
    blockchain: str,
) -> dict[str, str | None] | None:
    """Last-resort enrichment only; it never decides whether a token exists."""
    url = (
        "https://api.dexscreener.com/latest/dex/tokens/"
        f"{quote(contract_address, safe='')}"
    )
    payload = await _get_json(client, url, source="DexScreener")
    pairs = (payload or {}).get("pairs") if isinstance(payload, dict) else None
    if not isinstance(pairs, list):
        return None

    chain_id = {
        "Ethereum": "ethereum",
        "Robinhood": "robinhood",
        "BNB Chain": "bsc",
        "Polygon": "polygon",
        "Arbitrum": "arbitrum",
        "Avalanche": "avalanche",
        "Fantom": "fantom",
        "Solana": "solana",
        "Base": "base",
        "Cronos": "cronos",
        "Kava": "kava",
        "TRON": "tron",
        "TON": "ton",
        "SUI": "sui",
    }.get(blockchain)
    matching_pairs = [
        pair for pair in pairs
        if isinstance(pair, dict) and (not chain_id or pair.get("chainId") == chain_id)
    ]
    if not matching_pairs:
        return None

    pair = max(
        matching_pairs,
        key=lambda item: (item.get("liquidity") or {}).get("usd") or 0,
    )
    requested = contract_address.lower()
    base_token = pair.get("baseToken") or {}
    quote_token = pair.get("quoteToken") or {}
    token = (
        base_token
        if str(base_token.get("address", "")).lower() == requested
        else quote_token
    )
    info = pair.get("info") or {}
    return _metadata(
        token.get("name") or token.get("symbol"),
        token.get("symbol"),
        info.get("imageUrl"),
        "DexScreener",
        pair_url=pair.get("url"),
        author=pair.get("author") or info.get("author"),
        price_usd=pair.get("priceUsd"),
        volume_24h=(pair.get("volume") or {}).get("h24")
        if isinstance(pair.get("volume"), dict)
        else None,
        exchange=pair.get("dexId"),
    ) or None


def _trust_wallet_image(contract_address: str, blockchain: str) -> str | None:
    chain = TRUST_WALLET_CHAINS.get(blockchain)
    if not chain:
        return None
    return (
        "https://raw.githubusercontent.com/trustwallet/assets/master/"
        f"blockchains/{chain}/assets/{quote(contract_address, safe='')}/logo.png"
    )


def _merge_metadata(
    results: list[dict[str, str | None]],
    contract_address: str,
    blockchain: str,
) -> dict[str, str | None] | None:
    merged: dict[str, str | None] = {}
    sources: list[str] = []
    for result in results:
        for key, value in result.items():
            if value and key not in merged:
                merged[key] = value
        source = result.get("source")
        if source and source not in sources:
            sources.append(source)

    if not merged.get("name") and not merged.get("symbol"):
        return None
    merged["name"] = merged.get("name") or merged.get("symbol")
    merged["source"] = " + ".join(sources)
    if not merged.get("image_url"):
        merged["image_url"] = _trust_wallet_image(contract_address, blockchain)
    return merged


async def find_token_metadata(
    contract_address: str,
    blockchain: str,
    include_market_data: bool = False,
) -> dict[str, str | None] | None:
    """Find token metadata from multiple indexes, then from the chain itself."""
    address = (contract_address or "").strip()
    if not address:
        return None

    timeout = httpx.Timeout(8.0, connect=5.0)
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": "DEX-Telegram-Bot/1.0"},
    ) as client:
        lookups = [
            _lookup_pumpfun(client, address, blockchain),
            _lookup_jupiter(client, address, blockchain),
            _lookup_geckoterminal(client, address, blockchain),
            _lookup_coingecko(client, address, blockchain),
            _lookup_evm_onchain(client, address, blockchain),
        ]
        results = await asyncio.gather(*lookups, return_exceptions=True)
        metadata = [
            result
            for result in results
            if isinstance(result, dict) and result.get("name")
        ]

        # DexScreener is intentionally last: it can enrich a token already
        # identified elsewhere, but an absent pair must never reject the CA.
        if (
            include_market_data
            or not metadata
            or not any(item.get("image_url") for item in metadata)
        ):
            dexscreener = await _lookup_dexscreener(client, address, blockchain)
            if dexscreener:
                metadata.append(dexscreener)

        return _merge_metadata(metadata, address, blockchain)