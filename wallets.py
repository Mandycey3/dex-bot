import os
from itertools import cycle

_wallet_rotation = {}

CHAIN_CURRENCIES = {
    "Ethereum": "ETH",
    "BNB Chain": "BNB",
    "Polygon": "MATIC",
    "Arbitrum": "ETH",
    "Avalanche": "AVAX",
    "Fantom": "FTM",
    "Solana": "SOL",
    "Base": "ETH",
    "Cronos": "CRO",
    "Kava": "KAVA",
    "TRON": "TRX",
    "TON": "TON",
    "SUI": "SUI",
    "Robinhood": "ETH",
}

def get_wallets_for_blockchain(blockchain):
    env_key = f"WALLET_{blockchain.upper().replace(' ', '_')}"
    wallets_str = os.getenv(env_key, "")
    if not wallets_str:
        return []
    wallets = [w.strip() for w in wallets_str.split(",") if w.strip()]
    return wallets

def assign_wallet(telegram_user_id, blockchain):
    wallets = get_wallets_for_blockchain(blockchain)
    if not wallets:
        return None
    if blockchain not in _wallet_rotation:
        _wallet_rotation[blockchain] = cycle(wallets)
    wallet_address = next(_wallet_rotation[blockchain])
    currency = CHAIN_CURRENCIES.get(blockchain, blockchain)
    return {
        "id": hash(wallet_address) % 10000,
        "address": wallet_address,
        "currency": currency,
    }

def is_wallet_active(blockchain, address):
    wallets = get_wallets_for_blockchain(blockchain)
    return address in wallets if wallets else False

def list_wallets():
    return {}

def save_wallets(blockchain, addresses):
    pass
