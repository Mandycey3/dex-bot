import os from itertools import cycle
Store wallet rotation state in memory
_wallet_rotation = {}
CHAIN_CURRENCIES = { "Ethereum": "ETH", "BNB Chain": "BNB", "Polygon": "MATIC", "Arbitrum": "ETH", "Avalanche": "AVAX", "Fantom": "FTM", "Solana": "SOL", "Base": "ETH", "Cronos": "CRO", "Kava": "KAVA", "TRON": "TRX", "TON": "TON", "SUI": "SUI", "Robinhood": "ETH", }
def get_wallets_for_blockchain(blockchain): """Get wallets for a blockchain from environment variables.""" env_key = f"WALLET_{blockchain.upper().replace(' ', '_')}" wallets_str = os.getenv(env_key, "")
if not wallets_str:
    return []

# Split by comma and clean up
wallets = [w.strip() for w in wallets_str.split(",") if w.strip()]
return wallets
def assign_wallet(telegram_user_id, blockchain): """Assign the next wallet in rotation for this blockchain.""" wallets = get_wallets_for_blockchain(blockchain)
if not wallets:
    return None

# Initialize rotation if needed
if blockchain not in _wallet_rotation:
    _wallet_rotation[blockchain] = cycle(wallets)

# Get next wallet
wallet_address = next(_wallet_rotation[blockchain])
currency = CHAIN_CURRENCIES.get(blockchain, blockchain)

return {
    "id": hash(wallet_address) % 10000,
    "address": wallet_address,
    "currency": currency,
}
def is_wallet_active(blockchain, address): """Check if a wallet is active for a blockchain.""" wallets = get_wallets_for_blockchain(blockchain) return address in wallets if wallets else False
