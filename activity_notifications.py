import html
import logging
import os
from datetime import datetime, timezone

from telegram import Update


logger = logging.getLogger(__name__)


def _parse_chat_ids(value):
    chat_ids = set()
    for part in (value or "").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            chat_ids.add(int(part))
        except ValueError:
            logger.warning("Ignoring invalid Telegram chat ID in activity settings")
    return chat_ids


def _configured_owner_chat_id():
    value = os.getenv("BOT_ACTIVITY_OWNER_CHAT_ID", "").strip()
    try:
        return int(value) if value else None
    except ValueError:
        logger.warning("BOT_ACTIVITY_OWNER_CHAT_ID is not a valid Telegram chat ID")
        return None


def _admin_chat_ids():
    configured = _parse_chat_ids(os.getenv("BOT_ACTIVITY_ADMIN_CHAT_IDS", ""))
    owner_chat_id = _configured_owner_chat_id()
    if owner_chat_id is not None:
        configured.add(owner_chat_id)
    return configured


def should_notify_activity(update: Update):
    owner_chat_id = _configured_owner_chat_id()
    if owner_chat_id is None:
        return False

    user_id = update.effective_user.id if update.effective_user else None
    chat_id = update.effective_chat.id if update.effective_chat else None
    admin_ids = _admin_chat_ids()
    return user_id not in admin_ids and chat_id not in admin_ids


def _activity_description(update: Update):
    if update.callback_query:
        callback = update.callback_query
        return f"Button: {callback.data or '(no callback data)'}"

    if update.message:
        message = update.message
        text = message.text or message.caption
        if text:
            label = "Command" if text.startswith("/") else "Message"
            return f"{label}: {text}"
        if message.photo:
            return "Photo message"
        if message.document:
            return "Document message"
        if message.video:
            return "Video message"
        if message.voice:
            return "Voice message"
        return "Message without text"

    if update.edited_message:
        return "Edited message"
    if update.channel_post:
        return "Channel post"
    return f"Telegram update: {type(update).__name__}"


def format_activity_notification(update: Update):
    user = update.effective_user
    chat = update.effective_chat
    display_name = (
        " ".join(
            part
            for part in (getattr(user, "first_name", ""), getattr(user, "last_name", ""))
            if part
        )
        or "Unknown user"
    )
    username = f"@{user.username}" if user and user.username else "no username"
    user_id = str(user.id) if user else "unknown"
    chat_id = str(chat.id) if chat else "unknown"
    activity = _activity_description(update)
    if len(activity) > 2800:
        activity = f"{activity[:2800]}…"

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return (
        "🔔 <b>Bot Activity</b>\n\n"
        f"<b>User:</b> {html.escape(display_name)} ({html.escape(username)})\n"
        f"<b>User ID:</b> <code>{html.escape(user_id)}</code>\n"
        f"<b>Chat ID:</b> <code>{html.escape(chat_id)}</code>\n"
        f"<b>Time:</b> {timestamp}\n\n"
        f"<b>Action:</b>\n{html.escape(activity)}"
    )


async def send_activity_notification(update: Update, bot):
    owner_chat_id = _configured_owner_chat_id()
    if owner_chat_id is None or not should_notify_activity(update):
        return
    try:
        await bot.send_message(
            chat_id=owner_chat_id,
            text=format_activity_notification(update),
        )
    except Exception:
        logger.exception("Could not send bot activity notification")


async def activity_notification_handler(update: Update, context):
    if not should_notify_activity(update):
        return
    context.application.create_task(
        send_activity_notification(update, context.bot),
        update=update,
    )