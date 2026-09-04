import os

import psycopg


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    return psycopg.connect(database_url)


def is_user_banned(telegram_user_id):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM banned_users
                WHERE telegram_user_id = %s
                LIMIT 1
                """,
                (telegram_user_id,),
            )
            return cursor.fetchone() is not None


def ban_user(telegram_user_id, reason=None):
    reason = (reason or "").strip()[:500] or None
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO banned_users (telegram_user_id, reason)
                VALUES (%s, %s)
                ON CONFLICT (telegram_user_id)
                DO UPDATE SET reason = EXCLUDED.reason, updated_at = NOW()
                """,
                (telegram_user_id, reason),
            )


def unban_user(telegram_user_id):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM banned_users
                WHERE telegram_user_id = %s
                """,
                (telegram_user_id,),
            )
            return cursor.rowcount > 0


def list_banned_users():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT telegram_user_id, reason, banned_at, updated_at
                FROM banned_users
                ORDER BY banned_at DESC
                """
            )
            columns = [column.name for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]