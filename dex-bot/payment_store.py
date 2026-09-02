import os
from decimal import Decimal

import psycopg
from psycopg.errors import UniqueViolation


class DuplicateTransactionError(Exception):
    """Raised when a transaction hash is already reserved or confirmed."""


class PaymentStateError(Exception):
    """Raised when a payment cannot be updated from its current state."""


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    return psycopg.connect(database_url)


def _payment_from_row(cursor, row):
    if row is None:
        return None
    return dict(zip((column.name for column in cursor.description), row))


def create_payment(
    telegram_user_id,
    service,
    platform,
    tier,
    blockchain,
    currency,
    token_address,
    token_name,
    expected_amount,
    expected_amount_text,
    recipient_address,
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO payments (
                    telegram_user_id,
                    service,
                    platform,
                    tier,
                    blockchain,
                    currency,
                    token_address,
                    token_name,
                    expected_amount,
                    expected_amount_text,
                    recipient_address,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'awaiting_hash')
                RETURNING id
                """,
                (
                    telegram_user_id,
                    service,
                    platform,
                    tier,
                    blockchain,
                    currency,
                    token_address,
                    token_name,
                    expected_amount,
                    expected_amount_text,
                    recipient_address,
                ),
            )
            payment_id = cursor.fetchone()[0]
    return payment_id


def get_payment(payment_id, telegram_user_id):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, telegram_user_id, service, platform, tier,
                       blockchain, currency, token_address, token_name,
                       expected_amount, expected_amount_text,
                       recipient_address, transaction_hash, status,
                       verification_attempts, last_checked_at,
                       confirmed_at, failure_reason, fulfillment_status,
                       fulfillment_queued_at, created_at, updated_at
                FROM payments
                WHERE id = %s AND telegram_user_id = %s
                LIMIT 1
                """,
                (payment_id, telegram_user_id),
            )
            return _payment_from_row(cursor, cursor.fetchone())


def claim_transaction(payment_id, telegram_user_id, transaction_hash):
    """Reserve a hash before network verification to prevent race conditions."""
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE payments
                    SET transaction_hash = %s,
                        status = 'verifying',
                        failure_reason = NULL,
                        updated_at = NOW()
                    WHERE id = %s
                      AND telegram_user_id = %s
                      AND status IN (
                          'awaiting_hash',
                          'not_received',
                          'rejected',
                          'unsupported',
                          'timeout'
                      )
                    RETURNING id, telegram_user_id, service, platform, tier,
                              blockchain, currency, token_address, token_name,
                              expected_amount, expected_amount_text,
                              recipient_address, transaction_hash, status,
                              verification_attempts, last_checked_at,
                              confirmed_at, failure_reason, fulfillment_status,
                              fulfillment_queued_at, created_at, updated_at
                    """,
                    (transaction_hash, payment_id, telegram_user_id),
                )
                row = cursor.fetchone()
                if row is not None:
                    return _payment_from_row(cursor, row)

                cursor.execute(
                    """
                    SELECT id, telegram_user_id, service, platform, tier,
                           blockchain, currency, token_address, token_name,
                           expected_amount, expected_amount_text,
                           recipient_address, transaction_hash, status,
                           verification_attempts, last_checked_at,
                           confirmed_at, failure_reason, fulfillment_status,
                           fulfillment_queued_at, created_at, updated_at
                    FROM payments
                    WHERE id = %s AND telegram_user_id = %s
                    LIMIT 1
                    """,
                    (payment_id, telegram_user_id),
                )
                existing = _payment_from_row(cursor, cursor.fetchone())
                if existing is None:
                    raise PaymentStateError("Payment order could not be found.")
                if existing["status"] == "confirmed":
                    raise DuplicateTransactionError(
                        "This payment has already been confirmed."
                    )
                if existing["status"] == "verifying":
                    raise PaymentStateError(
                        "This payment is already being verified."
                    )
                raise PaymentStateError(
                    "This payment is not available for another transaction hash."
                )
    except UniqueViolation as error:
        raise DuplicateTransactionError(
            "This transaction hash has already been submitted."
        ) from error


def record_verification_attempt(payment_id):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE payments
                SET verification_attempts = verification_attempts + 1,
                    last_checked_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s
                """,
                (payment_id,),
            )


def mark_payment_confirmed(payment_id, transaction_hash):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE payments
                SET status = 'confirmed',
                    transaction_hash = %s,
                    confirmed_at = NOW(),
                    fulfillment_status = 'queued',
                    fulfillment_queued_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s
                  AND status = 'verifying'
                RETURNING id
                """,
                (transaction_hash, payment_id),
            )
            if cursor.fetchone() is None:
                raise PaymentStateError(
                    "The payment changed before it could be confirmed."
                )


def mark_payment_not_received(payment_id, reason, status="not_received"):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE payments
                SET status = %s,
                    failure_reason = %s,
                    updated_at = NOW()
                WHERE id = %s
                  AND status = 'verifying'
                """,
                (status, reason, payment_id),
            )


def claim_fulfillment(payment_id):
    """Claim the queued fulfillment exactly once."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE payments
                SET fulfillment_status = 'processing',
                    updated_at = NOW()
                WHERE id = %s
                  AND status = 'confirmed'
                  AND fulfillment_status = 'queued'
                RETURNING id
                """,
                (payment_id,),
            )
            return cursor.fetchone() is not None