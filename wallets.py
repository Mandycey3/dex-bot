import os

import psycopg


CHAIN_CURRENCIES = {
    "Ethereum": "ETH",
    "Robinhood": "ETH",
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
}


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    return psycopg.connect(database_url)


def save_wallets(blockchain, addresses):
    currency = CHAIN_CURRENCIES[blockchain]
    cleaned_addresses = []
    seen = set()
    for address in addresses:
        address = address.strip()
        if address and address not in seen:
            cleaned_addresses.append(address)
            seen.add(address)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE wallets SET active = FALSE "
                "WHERE blockchain = %s",
                (blockchain,),
            )
            for rotation_order, address in enumerate(cleaned_addresses):
                cursor.execute(
                    """
                    INSERT INTO wallets (
                        blockchain, currency, address, rotation_order, active
                    )
                    VALUES (%s, %s, %s, %s, TRUE)
                    ON CONFLICT (blockchain, address)
                    DO UPDATE SET
                        currency = EXCLUDED.currency,
                        rotation_order = EXCLUDED.rotation_order,
                        active = TRUE
                    """,
                    (blockchain, currency, address, rotation_order),
                )
    return len(cleaned_addresses)


def list_wallets():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT blockchain, address, active, rotation_order
                FROM wallets
                ORDER BY blockchain, rotation_order, id
                """
            )
            rows = cursor.fetchall()

    wallets = {blockchain: [] for blockchain in CHAIN_CURRENCIES}
    for blockchain, address, active, rotation_order in rows:
        wallets.setdefault(blockchain, []).append(
            {
                "address": address,
                "active": active,
                "rotation_order": rotation_order,
            }
        )
    return wallets


def assign_wallet(telegram_user_id, blockchain):
    """Assign the least recently used active wallet for this order."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, address, currency
                FROM wallets
                WHERE blockchain = %s AND active = TRUE
                ORDER BY last_assigned_at NULLS FIRST,
                         rotation_order,
                         id
                LIMIT 1
                FOR UPDATE
                """,
                (blockchain,),
            )
            wallet = cursor.fetchone()
            if not wallet:
                return None

            wallet_id, address, currency = wallet
            cursor.execute(
                "UPDATE wallets SET last_assigned_at = NOW() WHERE id = %s",
                (wallet_id,),
            )
            cursor.execute(
                """
                INSERT INTO wallet_assignments (
                    telegram_user_id, blockchain, wallet_id
                )
                VALUES (%s, %s, %s)
                """,
                (telegram_user_id, blockchain, wallet_id),
            )

    return {
        "id": wallet_id,
        "address": address,
        "currency": currency,
    }


def is_wallet_active(blockchain, address):
    if not address:
        return False

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM wallets
                WHERE blockchain = %s AND address = %s AND active = TRUE
                LIMIT 1
                """,
                (blockchain, address),
            )
            return cursor.fetchone() is not None