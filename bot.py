import asyncio
from html import escape
import logging
import threading
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    Defaults,
    TypeHandler,
    ApplicationHandlerStop,
)
from config import (
    TELEGRAM_BOT_TOKEN,
    WELCOME_MESSAGE,
    ABOUT_MESSAGE,
    SUPPORT_MESSAGE,
    MAIN_MENU_BUTTONS,
    BLOCKCHAINS,
    DEXSCREENER_SERVICES,
    PUMPFUN_SERVICES,
    FOURMEME_SERVICES,
    FLAPSH_SERVICES,
)
from menus import (
    get_main_menu, get_service_message, get_blockchain_buttons,
    get_pumpfun_services_message, get_four_meme_services_message,
    get_flapsh_services_message,
    get_pumpfun_boost_tier_buttons,
    get_pumpfun_trending_tier_buttons,
    get_pumpfun_volume_tier_buttons,
    get_pumpfun_graduation_tier_buttons,
    get_four_meme_boost_tier_buttons,
    get_four_meme_trending_tier_buttons,
    get_four_meme_volume_tier_buttons,
    get_flapsh_boost_tier_buttons,
    get_flapsh_trending_tier_buttons,
    get_flapsh_volume_tier_buttons,
    get_pumpfun_token_info_message, get_pumpfun_token_confirmation_message,
    get_update_tier_message, get_update_tier_buttons,
    get_trending_tier_message, get_trending_tier_buttons,
    get_volume_tier_message, get_volume_tier_buttons,
    get_boost_tier_message, get_boost_tier_buttons,
    get_token_address_message, get_token_verification_message,
    get_project_info_message, get_token_confirmation_message,
    get_token_confirmation_buttons, get_update_token_info_message,
    get_update_logo_prompt, get_logo_received_message,
    get_banner_received_message, get_update_confirmation_message,
    get_update_confirmation_buttons,
    get_payment_message, get_payment_buttons,
    get_transaction_hash_message, get_transaction_hash_buttons,
    get_payment_checking_message, get_payment_not_received_message,
    get_payment_retry_buttons, get_payment_verified_message,
    get_social_links_message, get_social_media_buttons, get_inline_keyboard
)
from pricing import (
    DEXSCREENER_UPDATE_PRICING,
    DEXSCREENER_TRENDING_PRICING,
    DEXSCREENER_VOLUME_PRICING,
    DEXSCREENER_BOOST_PRICING,
    PUMPFUN_BOOST_PRICING,
    PUMPFUN_TRENDING_PRICING,
    PUMPFUN_VOLUME_PRICING,
    PUMPFUN_GRADUATION_PRICING,
    FOURMEME_BOOST_PRICING,
    FOURMEME_TRENDING_PRICING,
    FOURMEME_VOLUME_PRICING,
    FLAPSH_BOOST_PRICING,
    FLAPSH_TRENDING_PRICING,
    FLAPSH_VOLUME_PRICING,
)
from admin import start_admin_server
from wallets import assign_wallet, is_wallet_active
from blockchain_verifier import (
    VerificationResult,
    normalize_transaction_hash,
    parse_native_amount,
    verify_payment,
)
from payment_store import (
    DuplicateTransactionError,
    PaymentStateError,
    claim_transaction,
    create_payment,
    get_payment,
    claim_fulfillment,
    mark_payment_confirmed,
    mark_payment_not_received,
    record_verification_attempt,
)
from activity_notifications import (
    _admin_chat_ids,
    activity_notification_handler,
)
from token_metadata import find_token_metadata
from pumpfun_banner import create_pumpfun_banner
from user_bans import ban_user, is_user_banned, list_banned_users, unban_user

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
# Telegram request URLs include the bot token; keep them out of workflow logs.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# States for conversation
START, PLATFORM, SERVICE, BLOCKCHAIN, TIER, TOKEN_ADDRESS, TOKEN_CONFIRMATION, PAYMENT, SOCIAL_LINKS, TRANSACTION_HASH, UPDATE_MEDIA = range(11)

class BotState:
    """Store user state during conversation"""
    def __init__(self):
        self.user_data = {}
    
    def set_user(self, user_id, **kwargs):
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        self.user_data[user_id].update(kwargs)
    
    def get_user(self, user_id):
        return self.user_data.get(user_id, {})
    
    def clear_user(self, user_id):
        if user_id in self.user_data:
            del self.user_data[user_id]

bot_state = BotState()


async def blocked_user_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Stop banned users before activity or conversation handlers run."""
    telegram_user = update.effective_user
    if not telegram_user:
        return

    try:
        banned = is_user_banned(telegram_user.id)
    except Exception:
        logger.exception(
            "Could not check ban status for Telegram user %s",
            telegram_user.id,
        )
        return

    if not banned:
        return

    bot_state.clear_user(telegram_user.id)
    try:
        if update.callback_query:
            await update.callback_query.answer(
                "Your access to this bot is restricted.",
                show_alert=True,
            )
        elif update.message:
            await update.message.reply_text(
                "Your access to this bot is restricted. Please contact support."
            )
    except TelegramError:
        logger.debug(
            "Could not notify banned Telegram user %s",
            telegram_user.id,
        )
    raise ApplicationHandlerStop


def is_admin_update(update: Update) -> bool:
    """Return whether this Telegram user or chat may use admin controls."""
    admin_ids = _admin_chat_ids()
    user_id = update.effective_user.id if update.effective_user else None
    chat_id = update.effective_chat.id if update.effective_chat else None
    return user_id in admin_ids or chat_id in admin_ids


def admin_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🚫 Ban user", callback_data="admin:ban"),
                InlineKeyboardButton("✅ Unban user", callback_data="admin:unban"),
            ],
            [
                InlineKeyboardButton(
                    "📋 View banned users",
                    callback_data="admin:list",
                ),
            ],
        ]
    )


def format_banned_users():
    entries = list_banned_users()
    if not entries:
        return "📋 <b>Banned Users</b>\n\nNo users are currently banned."

    lines = ["📋 <b>Banned Users</b>", ""]
    for item in entries:
        reason = escape(item["reason"] or "No reason provided")
        banned_at = escape(str(item["banned_at"]))
        lines.append(
            f"• <code>{item['telegram_user_id']}</code> — "
            f"{reason}\n  <i>{banned_at}</i>"
        )
    return "\n".join(lines)


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Open the in-bot admin controls for configured admin IDs."""
    if not is_admin_update(update):
        await update.message.reply_text(
            "This command is only available to the bot administrator."
        )
        raise ApplicationHandlerStop

    context.user_data.pop("admin_action", None)
    await update.message.reply_text(
        "🛡 <b>Bot Admin Controls</b>\n\n"
        "Choose an action below. Payment history is never deleted when a user "
        "is banned.",
        reply_markup=admin_keyboard(),
    )
    raise ApplicationHandlerStop


def parse_admin_target(value):
    parts = value.strip().split(maxsplit=1)
    if not parts:
        raise ValueError("Enter a Telegram user ID.")
    try:
        user_id = int(parts[0])
    except ValueError as error:
        raise ValueError("Telegram user ID must be a number.") from error
    if user_id <= 0:
        raise ValueError("Telegram user ID must be positive.")
    return user_id, (parts[1].strip() if len(parts) > 1 else None)


async def apply_admin_action(update, context, action, value):
    if not is_admin_update(update):
        await update.message.reply_text(
            "This command is only available to the bot administrator."
        )
        raise ApplicationHandlerStop

    try:
        target_user_id, reason = parse_admin_target(value)
        if action == "ban":
            ban_user(target_user_id, reason)
            message = f"🚫 User <code>{target_user_id}</code> has been banned."
        else:
            removed = unban_user(target_user_id)
            message = (
                f"✅ User <code>{target_user_id}</code> has been unbanned."
                if removed
                else f"ℹ️ User <code>{target_user_id}</code> was not on the ban list."
            )
    except ValueError as error:
        message = f"❌ {escape(str(error))}"
    except Exception:
        logger.exception("Could not apply %s action from Telegram", action)
        message = (
            "❌ <b>Could not update the ban list.</b>\n\n"
            "Check that the database schema has been applied."
        )

    context.user_data.pop("admin_action", None)
    await update.message.reply_text(message)
    raise ApplicationHandlerStop


async def admin_ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a user with /ban USER_ID [reason]."""
    value = " ".join(context.args)
    if not value:
        await update.message.reply_text(
            "Usage: /ban <Telegram user ID> [optional reason]"
        )
        raise ApplicationHandlerStop
    await apply_admin_action(update, context, "ban", value)


async def admin_unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user with /unban USER_ID."""
    value = " ".join(context.args)
    if not value:
        await update.message.reply_text("Usage: /unban <Telegram user ID>")
        raise ApplicationHandlerStop
    await apply_admin_action(update, context, "unban", value)


async def handle_admin_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Handle Ban, Unban, and list buttons from the in-bot admin panel."""
    query = update.callback_query
    if not is_admin_update(update):
        await query.answer(
            "These controls are only available to the bot administrator.",
            show_alert=True,
        )
        raise ApplicationHandlerStop

    await query.answer()
    action = query.data.split(":", 1)[1]
    if action == "list":
        await query.message.reply_text(format_banned_users())
    elif action in {"ban", "unban"}:
        context.user_data["admin_action"] = action
        command = "/ban" if action == "ban" else "/unban"
        await query.message.reply_text(
            f"Send the Telegram user ID now, or use {command} directly.\n"
            + (
                "You may add a reason after the ID."
                if action == "ban"
                else ""
            )
        )
    raise ApplicationHandlerStop


async def handle_pending_admin_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Accept a user ID after the admin taps Ban or Unban."""
    if not update.message or not is_admin_update(update):
        return
    action = context.user_data.get("admin_action")
    if action not in {"ban", "unban"}:
        return
    await apply_admin_action(update, context, action, update.message.text or "")


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

def normalize_tier_name(selection: str) -> str:
    """Convert a button label into the key used by the pricing tables."""
    return selection.split(" (", 1)[0].strip()


def get_selected_pricing(service: str, blockchain: str, tier: str):
    """Return the configured price for the user's selected service and tier."""
    tier = normalize_tier_name(tier)

    if service == "DexScreener Update":
        return DEXSCREENER_UPDATE_PRICING.get("all_chains", {}).get(tier)
    if service == "DexScreener Trending":
        return DEXSCREENER_TRENDING_PRICING.get(blockchain, {}).get(tier)
    if service == "DexScreener Volume":
        return DEXSCREENER_VOLUME_PRICING.get(blockchain, {}).get(tier)
    if service == "DexScreener Boost":
        return DEXSCREENER_BOOST_PRICING.get(blockchain, {}).get(tier)
    if service == "Pump.fun Boost":
        return PUMPFUN_BOOST_PRICING.get(tier)
    if service == "Pump.fun Trending":
        return PUMPFUN_TRENDING_PRICING.get(tier)
    if service == "Pump.fun Volume":
        return PUMPFUN_VOLUME_PRICING.get(tier)
    if service == "Pump.fun Graduation":
        return PUMPFUN_GRADUATION_PRICING.get(tier)
    if service == "Four.Meme Boost":
        return FOURMEME_BOOST_PRICING.get(tier)
    if service == "Four.Meme Trending":
        return FOURMEME_TRENDING_PRICING.get(tier)
    if service == "Four.Meme Volume":
        return FOURMEME_VOLUME_PRICING.get(tier)
    if service == "Flap.sh Boost":
        return FLAPSH_BOOST_PRICING.get(tier)
    if service == "Flap.sh Trending":
        return FLAPSH_TRENDING_PRICING.get(tier)
    if service == "Flap.sh Volume":
        return FLAPSH_VOLUME_PRICING.get(tier)
    return None


def get_payment_details(
    service: str,
    blockchain: str,
    tier: str,
    wallet_address: str = None,
):
    """Resolve the payment amount and the wallet for the selected order."""
    pricing = get_selected_pricing(service, blockchain, tier)
    if not pricing:
        return "Price not configured", "Payment wallet not configured"

    amount = pricing["price"]
    currency = amount.rsplit(" ", 1)[-1] if not amount.startswith("$") else CHAIN_CURRENCIES.get(blockchain)
    return amount, wallet_address


async def _delete_message(message):
    try:
        await message.delete()
    except TelegramError as error:
        logger.debug("Could not delete message: %s", error)


async def _prepare_flow_message(update: Update):
    """Remove the previous step before sending the next flow message."""
    user_id = update.effective_user.id

    if update.callback_query:
        await _delete_message(update.callback_query.message)
        return

    user = bot_state.get_user(user_id)
    if not user.get("clean_flow_messages"):
        return

    for message_id in user.get("flow_message_ids", []):
        try:
            await update.get_bot().delete_message(
                chat_id=update.effective_chat.id,
                message_id=message_id,
            )
        except TelegramError as error:
            logger.debug("Could not delete flow message: %s", error)

    await _delete_message(update.message)
    bot_state.set_user(user_id, flow_message_ids=[])


def _remember_flow_message(user_id, message):
    user = bot_state.get_user(user_id)
    flow_message_ids = user.get("flow_message_ids", [])
    if message.message_id not in flow_message_ids:
        flow_message_ids.append(message.message_id)
    bot_state.set_user(
        user_id,
        last_bot_message_id=message.message_id,
        flow_message_ids=flow_message_ids,
    )


def get_update_text(update: Update) -> str:
    """Return text from a normal message or an inline-button callback."""
    if update.callback_query:
        return update.callback_query.data or ""
    if not update.message:
        return ""
    # Photo/document messages do not have Message.text. Returning an empty
    # string lets media handlers inspect the attachment without crashing.
    return update.message.text or ""


async def send_message(
    update: Update,
    text: str,
    reply_markup=None,
    preserve_previous=False,
):
    """Send a response while keeping the active service flow to one message."""
    user_id = update.effective_user.id

    if update.callback_query:
        query = update.callback_query
        await query.answer()
    preserve_history = bot_state.get_user(user_id).get(
        "preserve_chat_history",
        False,
    )
    if not preserve_previous and not preserve_history:
        await _prepare_flow_message(update)
    sent_message = await update.effective_chat.send_message(
        text,
        reply_markup=reply_markup,
    )

    _remember_flow_message(user_id, sent_message)
    return sent_message


async def send_photo(
    update: Update,
    photo_url: str,
    caption: str,
    reply_markup=None,
    preserve_previous=False,
):
    """Send a project logo with its order details as one flow message."""
    user_id = update.effective_user.id

    if update.callback_query:
        await update.callback_query.answer()

    if not preserve_previous:
        await _prepare_flow_message(update)
    sent_message = await update.effective_chat.send_photo(
        photo=photo_url,
        caption=caption,
        reply_markup=reply_markup,
    )

    _remember_flow_message(user_id, sent_message)
    return sent_message


async def edit_menu_message(update: Update, text: str, reply_markup=None):
    """Edit the current inline menu instead of creating a new message."""
    if not update.callback_query:
        return await send_message(update, text, reply_markup=reply_markup)

    query = update.callback_query
    await query.answer()
    try:
        edited_message = await query.edit_message_text(
            text,
            reply_markup=reply_markup,
        )
    except TelegramError as error:
        logger.warning("Could not edit inline menu: %s", error)
        return await send_message(update, text, reply_markup=reply_markup)

    _remember_flow_message(update.effective_user.id, edited_message)
    return edited_message


async def handle_reply_keyboard_navigation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Handle persistent reply-keyboard navigation from any conversation state."""
    if update.callback_query or not update.message:
        return None

    text = update.message.text
    user_id = update.effective_user.id
    main_buttons = {
        button
        for row in MAIN_MENU_BUTTONS
        for button in row
    }
    service_buttons = {
        button
        for row in DEXSCREENER_SERVICES
        for button in row
    }
    pumpfun_service_buttons = {
        button
        for row in PUMPFUN_SERVICES
        for button in row
        if button != "🔙 Back to Main Menu"
    }
    four_meme_service_buttons = {
        button
        for row in FOURMEME_SERVICES
        for button in row
        if button != "🔙 Back to Main Menu"
    }
    flapsh_service_buttons = {
        button
        for row in FLAPSH_SERVICES
        for button in row
        if button != "🔙 Back to Main Menu"
    }

    if text == "DexScreener":
        bot_state.clear_user(user_id)
        bot_state.set_user(user_id, platform="DexScreener")
        markup = ReplyKeyboardMarkup(DEXSCREENER_SERVICES, resize_keyboard=True)
        await send_message(update, get_main_menu(), reply_markup=markup)
        return SERVICE

    if text == "Pump.fun":
        bot_state.clear_user(user_id)
        bot_state.set_user(user_id, platform="Pump.fun")
        markup = ReplyKeyboardMarkup(PUMPFUN_SERVICES, resize_keyboard=True)
        await send_message(update, get_pumpfun_services_message(), reply_markup=markup)
        return SERVICE

    if text == "Four.Meme":
        bot_state.clear_user(user_id)
        bot_state.set_user(user_id, platform="Four.Meme")
        markup = ReplyKeyboardMarkup(FOURMEME_SERVICES, resize_keyboard=True)
        await send_message(
            update,
            get_four_meme_services_message(),
            reply_markup=markup,
        )
        return SERVICE

    if text == "Flap.sh":
        bot_state.clear_user(user_id)
        bot_state.set_user(user_id, platform="Flap.sh")
        markup = ReplyKeyboardMarkup(FLAPSH_SERVICES, resize_keyboard=True)
        await send_message(
            update,
            get_flapsh_services_message(),
            reply_markup=markup,
        )
        return SERVICE

    if text == "About":
        bot_state.clear_user(user_id)
        markup = ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True)
        await send_message(
            update,
            ABOUT_MESSAGE,
            reply_markup=markup,
        )
        return PLATFORM

    if text == "Support":
        bot_state.clear_user(user_id)
        markup = ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True)
        await send_message(
            update,
            SUPPORT_MESSAGE,
            reply_markup=markup,
        )
        return PLATFORM

    if text in pumpfun_service_buttons:
        bot_state.clear_user(user_id)
        bot_state.set_user(
            user_id,
            platform="Pump.fun",
            service=text,
            blockchain="Solana",
        )
        assigned_wallet = None
        try:
            assigned_wallet = assign_wallet(user_id, "Solana")
        except Exception as error:
            logger.error("Could not assign a Solana wallet: %s", error)
        bot_state.set_user(
            user_id,
            wallet_address=(
                assigned_wallet["address"] if assigned_wallet else None
            ),
        )
        tier_buttons = (
            get_pumpfun_boost_tier_buttons()
            if text == "Pump.fun Boost"
            else (
                get_pumpfun_trending_tier_buttons()
                if text == "Pump.fun Trending"
                else (
                    get_pumpfun_volume_tier_buttons()
                    if text == "Pump.fun Volume"
                    else get_pumpfun_graduation_tier_buttons()
                )
            )
        )
        await send_message(
            update,
            get_service_message(text),
            reply_markup=get_inline_keyboard(tier_buttons),
        )
        return TIER

    if text in four_meme_service_buttons:
        bot_state.clear_user(user_id)
        bot_state.set_user(
            user_id,
            platform="Four.Meme",
            service=text,
            blockchain="BNB Chain",
        )
        assigned_wallet = None
        try:
            assigned_wallet = assign_wallet(user_id, "BNB Chain")
        except Exception as error:
            logger.error("Could not assign a BNB Chain wallet: %s", error)
        bot_state.set_user(
            user_id,
            wallet_address=(
                assigned_wallet["address"] if assigned_wallet else None
            ),
        )
        tier_buttons = (
            get_four_meme_boost_tier_buttons()
            if text == "Four.Meme Boost"
            else (
                get_four_meme_trending_tier_buttons()
                if text == "Four.Meme Trending"
                else get_four_meme_volume_tier_buttons()
            )
        )
        await send_message(
            update,
            get_service_message(text),
            reply_markup=get_inline_keyboard(tier_buttons),
        )
        return TIER

    if text in flapsh_service_buttons:
        bot_state.clear_user(user_id)
        bot_state.set_user(
            user_id,
            platform="Flap.sh",
            service=text,
            blockchain="BNB Chain",
        )
        assigned_wallet = None
        try:
            assigned_wallet = assign_wallet(user_id, "BNB Chain")
        except Exception as error:
            logger.error("Could not assign a BNB Chain wallet: %s", error)
        bot_state.set_user(
            user_id,
            wallet_address=(
                assigned_wallet["address"] if assigned_wallet else None
            ),
        )
        tier_buttons = (
            get_flapsh_boost_tier_buttons()
            if text == "Flap.sh Boost"
            else (
                get_flapsh_trending_tier_buttons()
                if text == "Flap.sh Trending"
                else get_flapsh_volume_tier_buttons()
            )
        )
        await send_message(
            update,
            get_service_message(text),
            reply_markup=get_inline_keyboard(tier_buttons),
        )
        return TIER

    if text in service_buttons:
        if text == "🔙 Back to Main Menu":
            bot_state.clear_user(user_id)
            markup = ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True)
            await send_message(update, WELCOME_MESSAGE, reply_markup=markup)
            return PLATFORM

        bot_state.clear_user(user_id)
        bot_state.set_user(
            user_id,
            platform="DexScreener",
            service=text,
        )
        markup = get_inline_keyboard(get_blockchain_buttons())
        await send_message(update, get_service_message(text), reply_markup=markup)
        return BLOCKCHAIN

    if text in main_buttons:
        return None
    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start command and show main menu"""
    user_id = update.effective_user.id
    bot_state.clear_user(user_id)
    
    # Create main menu keyboard
    reply_keyboard = MAIN_MENU_BUTTONS
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    await send_message(update, WELCOME_MESSAGE, reply_markup=markup)
    return PLATFORM

async def handle_platform(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle platform selection"""
    navigated_state = await handle_reply_keyboard_navigation(update, context)
    if navigated_state is not None:
        return navigated_state

    text = get_update_text(update)
    user_id = update.effective_user.id
    
    if text == "DexScreener":
        bot_state.set_user(user_id, platform="DexScreener")
        
        # Show DexScreener services
        reply_keyboard = DEXSCREENER_SERVICES
        markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
        
        await send_message(update, get_main_menu(), reply_markup=markup)
        return SERVICE
    
    elif text == "Pump.fun":
        bot_state.clear_user(user_id)
        bot_state.set_user(user_id, platform="Pump.fun")
        reply_keyboard = PUMPFUN_SERVICES
        markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
        await send_message(update, get_pumpfun_services_message(), reply_markup=markup)
        return SERVICE

    elif text == "Four.Meme":
        bot_state.clear_user(user_id)
        bot_state.set_user(user_id, platform="Four.Meme")
        reply_keyboard = FOURMEME_SERVICES
        markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
        await send_message(
            update,
            get_four_meme_services_message(),
            reply_markup=markup,
        )
        return SERVICE

    elif text == "Flap.sh":
        bot_state.clear_user(user_id)
        bot_state.set_user(user_id, platform="Flap.sh")
        reply_keyboard = FLAPSH_SERVICES
        markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
        await send_message(
            update,
            get_flapsh_services_message(),
            reply_markup=markup,
        )
        return SERVICE

    elif text == "About":
        reply_keyboard = MAIN_MENU_BUTTONS
        markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
        await send_message(update, ABOUT_MESSAGE, reply_markup=markup)
        return PLATFORM
    
    elif text == "Support":
        reply_keyboard = MAIN_MENU_BUTTONS
        markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
        await send_message(update, SUPPORT_MESSAGE, reply_markup=markup)
        return PLATFORM
    
    else:
        await send_message(update,
            "❌ <b>Invalid selection.</b>\n\nPlease choose a platform from the menu."
        )
        return PLATFORM

async def handle_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle service selection"""
    navigated_state = await handle_reply_keyboard_navigation(update, context)
    if navigated_state is not None:
        return navigated_state

    text = get_update_text(update)
    user_id = update.effective_user.id
    
    valid_services = [
        "DexScreener Update",
        "DexScreener Trending",
        "DexScreener Volume",
        "DexScreener Boost",
        "Pump.fun Boost",
        "Pump.fun Trending",
        "Pump.fun Volume",
        "Pump.fun Graduation",
        "Four.Meme Boost",
        "Four.Meme Trending",
        "Four.Meme Volume",
        "Flap.sh Boost",
        "Flap.sh Trending",
        "Flap.sh Volume",
    ]

    if text == "🔙 Back to Main Menu":
        bot_state.clear_user(user_id)
        markup = ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True)
        await send_message(update, WELCOME_MESSAGE, reply_markup=markup)
        return PLATFORM
    
    if text in valid_services:
        bot_state.set_user(user_id, service=text)

        if text in [
            "Pump.fun Boost",
            "Pump.fun Trending",
            "Pump.fun Volume",
            "Pump.fun Graduation",
        ]:
            assigned_wallet = None
            try:
                assigned_wallet = assign_wallet(user_id, "Solana")
            except Exception as error:
                logger.error("Could not assign a Solana wallet: %s", error)
            bot_state.set_user(
                user_id,
                blockchain="Solana",
                wallet_address=(
                    assigned_wallet["address"] if assigned_wallet else None
                ),
            )
            tier_buttons = (
                get_pumpfun_boost_tier_buttons()
                if text == "Pump.fun Boost"
                else (
                    get_pumpfun_trending_tier_buttons()
                    if text == "Pump.fun Trending"
                    else (
                        get_pumpfun_volume_tier_buttons()
                        if text == "Pump.fun Volume"
                        else get_pumpfun_graduation_tier_buttons()
                    )
                )
            )
            await send_message(
                update,
                get_service_message(text),
                reply_markup=get_inline_keyboard(tier_buttons),
            )
            return TIER

        if text in [
            "Four.Meme Boost",
            "Four.Meme Trending",
            "Four.Meme Volume",
        ]:
            assigned_wallet = None
            try:
                assigned_wallet = assign_wallet(user_id, "BNB Chain")
            except Exception as error:
                logger.error("Could not assign a BNB Chain wallet: %s", error)
            bot_state.set_user(
                user_id,
                platform="Four.Meme",
                blockchain="BNB Chain",
                wallet_address=(
                    assigned_wallet["address"] if assigned_wallet else None
                ),
            )
            tier_buttons = (
                get_four_meme_boost_tier_buttons()
                if text == "Four.Meme Boost"
                else (
                    get_four_meme_trending_tier_buttons()
                    if text == "Four.Meme Trending"
                    else get_four_meme_volume_tier_buttons()
                )
            )
            await send_message(
                update,
                get_service_message(text),
                reply_markup=get_inline_keyboard(tier_buttons),
            )
            return TIER

        if text in [
            "Flap.sh Boost",
            "Flap.sh Trending",
            "Flap.sh Volume",
        ]:
            assigned_wallet = None
            try:
                assigned_wallet = assign_wallet(user_id, "BNB Chain")
            except Exception as error:
                logger.error("Could not assign a BNB Chain wallet: %s", error)
            bot_state.set_user(
                user_id,
                platform="Flap.sh",
                blockchain="BNB Chain",
                wallet_address=(
                    assigned_wallet["address"] if assigned_wallet else None
                ),
            )
            tier_buttons = (
                get_flapsh_boost_tier_buttons()
                if text == "Flap.sh Boost"
                else (
                    get_flapsh_trending_tier_buttons()
                    if text == "Flap.sh Trending"
                    else get_flapsh_volume_tier_buttons()
                )
            )
            await send_message(
                update,
                get_service_message(text),
                reply_markup=get_inline_keyboard(tier_buttons),
            )
            return TIER

        # Show blockchain selection
        reply_keyboard = get_blockchain_buttons()
        message = get_service_message(text)
        markup = get_inline_keyboard(reply_keyboard)
        await send_message(update, message, reply_markup=markup)
        return BLOCKCHAIN
    
    elif text == "🔙 Back to Main Menu":
        # Reset and go back to main menu
        bot_state.clear_user(user_id)
        reply_keyboard = MAIN_MENU_BUTTONS
        markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "<b>Main Menu</b>\n\nChoose an option below.",
            reply_markup=markup,
        )
        return PLATFORM
    
    else:
        await send_message(update,
            "❌ <b>Invalid selection.</b>\n\nPlease choose a service from the menu."
        )
        return SERVICE

async def handle_blockchain(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle blockchain selection"""
    navigated_state = await handle_reply_keyboard_navigation(update, context)
    if navigated_state is not None:
        return navigated_state

    text = get_update_text(update)
    user_id = update.effective_user.id
    user = bot_state.get_user(user_id)
    service = user.get("service")
    
    if text in BLOCKCHAINS:
        assigned_wallet = None
        try:
            assigned_wallet = assign_wallet(user_id, text)
        except Exception as error:
            logger.error("Could not assign a wallet for %s: %s", text, error)

        bot_state.set_user(
            user_id,
            blockchain=text,
            wallet_address=assigned_wallet["address"] if assigned_wallet else None,
            clean_flow_messages=True,
        )
        
        # Determine next step based on service
        if service == "DexScreener Update":
            reply_keyboard = get_update_tier_buttons()
            markup = get_inline_keyboard(reply_keyboard)
            await edit_menu_message(update, get_update_tier_message(), reply_markup=markup)
            return TIER
        
        elif service == "DexScreener Trending":
            reply_keyboard = get_trending_tier_buttons(text)
            markup = get_inline_keyboard(reply_keyboard)
            await edit_menu_message(
                update,
                get_trending_tier_message(text),
                reply_markup=markup,
            )
            return TIER
        
        elif service == "DexScreener Volume":
            reply_keyboard = get_volume_tier_buttons(text)
            markup = get_inline_keyboard(reply_keyboard)
            await edit_menu_message(
                update,
                get_volume_tier_message(text),
                reply_markup=markup,
            )
            return TIER
        
        elif service == "DexScreener Boost":
            reply_keyboard = get_boost_tier_buttons(text)
            markup = get_inline_keyboard(reply_keyboard)
            await edit_menu_message(
                update,
                get_boost_tier_message(text),
                reply_markup=markup,
            )
            return TIER
    
    elif text == "🔙 Back to Services":
        reply_keyboard = DEXSCREENER_SERVICES
        markup = get_inline_keyboard(reply_keyboard)
        await send_message(update, get_main_menu(), reply_markup=markup)
        return SERVICE
    
    else:
        await send_message(update,
            "❌ <b>Invalid blockchain.</b>\n\nPlease choose one of the listed networks."
        )
        return BLOCKCHAIN

async def handle_tier(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle tier selection"""
    navigated_state = await handle_reply_keyboard_navigation(update, context)
    if navigated_state is not None:
        return navigated_state

    text = get_update_text(update)
    user_id = update.effective_user.id
    user = bot_state.get_user(user_id)
    service = user.get("service")
    blockchain = user.get("blockchain")
    
    if text in ["🔙 Back", "🔙 Back to Blockchain"]:
        # Go back to blockchain selection
        reply_keyboard = get_blockchain_buttons()
        markup = get_inline_keyboard(reply_keyboard)
        await send_message(update, get_service_message(service), reply_markup=markup)
        return BLOCKCHAIN

    if text == "🔙 Back to Main Menu" and user.get("platform") == "Pump.fun":
        bot_state.clear_user(user_id)
        await send_message(
            update,
            WELCOME_MESSAGE,
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True),
        )
        return PLATFORM

    if text == "🔙 Back to Pump.fun Services":
        bot_state.clear_user(user_id)
        bot_state.set_user(user_id, platform="Pump.fun")
        await send_message(
            update,
            get_pumpfun_services_message(),
            reply_markup=ReplyKeyboardMarkup(PUMPFUN_SERVICES, resize_keyboard=True),
        )
        return SERVICE
    
    # Normalize the button label to the pricing-table key.
    tier_name = normalize_tier_name(text)
    selected_pricing = get_selected_pricing(service, blockchain, tier_name)
    if not selected_pricing:
        await send_message(
            update,
            "❌ <b>Price unavailable.</b>\n\n"
            "That option is not configured yet. Please choose another tier.",
        )
        return TIER

    # DexScreener starts cleaning the active flow after the blockchain choice.
    # Pump.fun has no blockchain screen, so start at the equivalent tier choice.
    bot_state.set_user(
        user_id,
        tier=tier_name,
        clean_flow_messages=True,
    )
    
    # Move to token address input
    reply_keyboard = [["🔙 Back to Tiers"], ["❌ Cancel"]]
    markup = get_inline_keyboard(reply_keyboard)
    await send_message(update, get_token_address_message(blockchain), reply_markup=markup)
    return TOKEN_ADDRESS

async def handle_token_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle token address input"""
    navigated_state = await handle_reply_keyboard_navigation(update, context)
    if navigated_state is not None:
        return navigated_state

    text = get_update_text(update)
    user_id = update.effective_user.id
    
    if text == "❌ Cancel":
        bot_state.clear_user(user_id)
        reply_keyboard = MAIN_MENU_BUTTONS
        markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
        await send_message(update,
            "❌ <b>Cancelled.</b>\n\nBack to the main menu.",
            reply_markup=markup,
        )
        return PLATFORM
    
    elif text == "🔙 Back to Tiers":
        user = bot_state.get_user(user_id)
        service = user.get("service")
        blockchain = user.get("blockchain")
        
        if service == "DexScreener Update":
            reply_keyboard = get_update_tier_buttons()
            markup = get_inline_keyboard(reply_keyboard)
            await send_message(update, get_update_tier_message(), reply_markup=markup)
        elif service == "DexScreener Trending":
            reply_keyboard = get_trending_tier_buttons(blockchain)
            markup = get_inline_keyboard(reply_keyboard)
            await send_message(
                update,
                get_trending_tier_message(blockchain),
                reply_markup=markup,
            )
        elif service == "DexScreener Volume":
            reply_keyboard = get_volume_tier_buttons(blockchain)
            markup = get_inline_keyboard(reply_keyboard)
            await send_message(
                update,
                get_volume_tier_message(blockchain),
                reply_markup=markup,
            )
        elif service == "DexScreener Boost":
            reply_keyboard = get_boost_tier_buttons(blockchain)
            markup = get_inline_keyboard(reply_keyboard)
            await send_message(
                update,
                get_boost_tier_message(blockchain),
                reply_markup=markup,
            )
        elif service == "Pump.fun Boost":
            reply_keyboard = get_pumpfun_boost_tier_buttons()
            markup = get_inline_keyboard(reply_keyboard)
            await send_message(
                update,
                get_service_message(service),
                reply_markup=markup,
            )
        elif service == "Pump.fun Trending":
            reply_keyboard = get_pumpfun_trending_tier_buttons()
            markup = get_inline_keyboard(reply_keyboard)
            await send_message(
                update,
                get_service_message(service),
                reply_markup=markup,
            )
        elif service == "Pump.fun Volume":
            reply_keyboard = get_pumpfun_volume_tier_buttons()
            markup = get_inline_keyboard(reply_keyboard)
            await send_message(
                update,
                get_service_message(service),
                reply_markup=markup,
            )
        elif service == "Pump.fun Graduation":
            reply_keyboard = get_pumpfun_graduation_tier_buttons()
            markup = get_inline_keyboard(reply_keyboard)
            await send_message(
                update,
                get_service_message(service),
                reply_markup=markup,
            )
        return TIER
    
    else:
        # Resolve metadata from multiple sources before asking for confirmation.
        bot_state.set_user(user_id, token_address=text)
        blockchain = bot_state.get_user(user_id).get("blockchain")
        project = await find_token_metadata(
            text,
            blockchain,
            include_market_data=(
                bot_state.get_user(user_id).get("service")
                in ["DexScreener Update", "Pump.fun Boost"]
                or bot_state.get_user(user_id).get("service")
                == "Pump.fun Trending"
                or bot_state.get_user(user_id).get("service")
                == "Pump.fun Volume"
                or bot_state.get_user(user_id).get("service")
                == "Pump.fun Graduation"
            ),
        )
        bot_state.set_user(user_id, project=project)

        service = bot_state.get_user(user_id).get("service")
        if service == "DexScreener Update":
            bot_state.set_user(
                user_id,
                update_stage="logo",
                logo_file_id=None,
                banner_file_id=None,
                socials={},
                pending_social=None,
            )
            project_info = get_update_token_info_message(project, blockchain, text)
        elif service == "Pump.fun Boost":
            project_info = get_pumpfun_token_info_message(project, text)
        else:
            project_info = get_project_info_message(project, blockchain, text)
        is_pumpfun_service = service in [
            "Pump.fun Boost",
            "Pump.fun Trending",
            "Pump.fun Volume",
            "Pump.fun Graduation",
        ]
        if is_pumpfun_service:
            project_data = project or {}
            try:
                banner = await create_pumpfun_banner(
                    project_data.get("image_url"),
                    project_data.get("name"),
                    project_data.get("symbol"),
                )
                await send_photo(
                    update,
                    banner,
                    project_info,
                    preserve_previous=True,
                )
            except Exception:
                logger.exception("Could not generate Pump.fun token banner")
                if project_data.get("image_url"):
                    try:
                        await send_photo(
                            update,
                            project_data["image_url"],
                            project_info,
                            preserve_previous=True,
                        )
                    except TelegramError as error:
                        logger.warning("Could not send token image: %s", error)
                        await send_message(update, project_info, preserve_previous=True)
                else:
                    await send_message(update, project_info, preserve_previous=True)
        elif project and project.get("image_url"):
            try:
                await send_photo(
                    update,
                    project["image_url"],
                    project_info,
                    preserve_previous=True,
                )
            except TelegramError as error:
                logger.warning("Could not send token image: %s", error)
                await send_message(update, project_info, preserve_previous=True)
        else:
            await send_message(update, project_info, preserve_previous=True)

        if service == "DexScreener Update":
            await send_message(
                update,
                get_update_logo_prompt(),
                reply_markup=get_inline_keyboard([["❌ Cancel"]]),
                preserve_previous=True,
            )
            return UPDATE_MEDIA

        confirmation_markup = get_inline_keyboard(get_token_confirmation_buttons())
        confirmation_message = (
            get_pumpfun_token_confirmation_message(service)
            if service in [
                "Pump.fun Boost",
                "Pump.fun Trending",
                "Pump.fun Volume",
                "Pump.fun Graduation",
            ]
            else get_token_confirmation_message(project, blockchain, text)
        )
        await send_message(
            update,
            confirmation_message,
            reply_markup=confirmation_markup,
            preserve_previous=True,
        )
        return TOKEN_CONFIRMATION


async def handle_token_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Confirm the DexScreener project before displaying payment details."""
    navigated_state = await handle_reply_keyboard_navigation(update, context)
    if navigated_state is not None:
        return navigated_state

    text = get_update_text(update)
    user_id = update.effective_user.id
    user = bot_state.get_user(user_id)
    blockchain = user.get("blockchain")

    if text in ["✅ Confirm Token", "Confirm Token"]:
        service = user.get("service", "").replace("DexScreener ", "")
        platform = user.get("platform", "DexScreener")
        tier = user.get("tier", "Unknown")
        amount, address = get_payment_details(
            user.get("service"),
            blockchain,
            tier,
            wallet_address=user.get("wallet_address"),
        )
        wallet_configured = False
        try:
            wallet_configured = is_wallet_active(
                blockchain,
                user.get("wallet_address"),
            )
        except Exception as error:
            logger.error(
                "Could not verify the payment wallet for %s: %s",
                blockchain,
                error,
            )

        if not wallet_configured or not address:
            await send_message(
                update,
                "<b>Payment wallet unavailable</b>\n\n"
                "No active payment wallet has been added for this blockchain yet.\n"
                "Please add a public wallet in the Wallet Admin page before accepting payment.",
                reply_markup=get_inline_keyboard(
                    [["🔙 Back to Tiers"], ["❌ Cancel"]]
                ),
            )
            return TOKEN_CONFIRMATION

        project = user.get("project")
        project_name = project["name"] if project else "Token metadata unavailable"
        payment_msg = get_payment_message(
            service,
            platform,
            tier,
            user.get("token_address", ""),
            amount,
            address,
            project_name=project_name,
        )
        markup = get_inline_keyboard(get_payment_buttons())
        await send_message(update, payment_msg, reply_markup=markup)
        return PAYMENT

    if text in ["🔄 Enter Different Address", "Enter Different Address"]:
        bot_state.set_user(
            user_id,
            project=None,
            update_stage=None,
            logo_file_id=None,
            banner_file_id=None,
            socials={},
            pending_social=None,
        )
        markup = get_inline_keyboard([["🔙 Back to Tiers"], ["❌ Cancel"]])
        await send_message(
            update,
            get_token_address_message(blockchain),
            reply_markup=markup,
        )
        return TOKEN_ADDRESS

    if text in ["🔙 Back to Tiers", "Back to Tiers"]:
        service = user.get("service")
        if service == "DexScreener Update":
            markup = get_inline_keyboard(get_update_tier_buttons())
            message = get_update_tier_message()
        elif service == "DexScreener Trending":
            markup = get_inline_keyboard(get_trending_tier_buttons(blockchain))
            message = get_trending_tier_message(blockchain)
        elif service == "DexScreener Boost":
            markup = get_inline_keyboard(get_boost_tier_buttons(blockchain))
            message = get_boost_tier_message(blockchain)
        elif service == "Pump.fun Boost":
            markup = get_inline_keyboard(get_pumpfun_boost_tier_buttons())
            message = get_service_message(service)
        elif service == "Pump.fun Trending":
            markup = get_inline_keyboard(get_pumpfun_trending_tier_buttons())
            message = get_service_message(service)
        elif service == "Pump.fun Volume":
            markup = get_inline_keyboard(get_pumpfun_volume_tier_buttons())
            message = get_service_message(service)
        elif service == "Pump.fun Graduation":
            markup = get_inline_keyboard(get_pumpfun_graduation_tier_buttons())
            message = get_service_message(service)
        else:
            markup = get_inline_keyboard(get_volume_tier_buttons(blockchain))
            message = get_volume_tier_message(blockchain)
        await send_message(update, message, reply_markup=markup)
        return TIER

    if text == "❌ Cancel":
        bot_state.clear_user(user_id)
        markup = ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True)
        await send_message(
            update,
            "❌ <b>Cancelled.</b>\n\nBack to the main menu.",
            reply_markup=markup,
        )
        return PLATFORM

    await send_message(
        update,
        "Please choose one of the confirmation options below.",
        reply_markup=get_inline_keyboard(get_token_confirmation_buttons()),
        preserve_previous=True,
    )
    return TOKEN_CONFIRMATION


def _incoming_photo_file_id(update):
    if not update.message:
        return None
    if update.message.photo:
        return update.message.photo[-1].file_id
    document = update.message.document
    if document:
        mime_type = (document.mime_type or "").lower()
        file_name = (document.file_name or "").lower()
        image_extensions = (
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".gif",
            ".bmp",
            ".avif",
        )
        if mime_type.startswith("image/") or file_name.endswith(image_extensions):
            return document.file_id
    return None


async def handle_update_media(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Collect the Update service logo and optional banner before socials."""
    navigated_state = await handle_reply_keyboard_navigation(update, context)
    if navigated_state is not None:
        return navigated_state

    user_id = update.effective_user.id
    user = bot_state.get_user(user_id)
    text = get_update_text(update)
    stage = user.get("update_stage", "logo")

    if text == "❌ Cancel":
        bot_state.clear_user(user_id)
        await send_message(
            update,
            "❌ <b>Cancelled.</b>\n\nBack to the main menu.",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True),
        )
        return PLATFORM

    photo_file_id = _incoming_photo_file_id(update)
    if stage == "logo":
        if not photo_file_id:
            await send_message(
                update,
                "Please send your <b>Project Logo</b> as an image.",
                reply_markup=get_inline_keyboard([["❌ Cancel"]]),
                preserve_previous=True,
            )
            return UPDATE_MEDIA
        bot_state.set_user(
            user_id,
            logo_file_id=photo_file_id,
            update_stage="banner",
        )
        await send_message(
            update,
            get_logo_received_message(),
            reply_markup=get_inline_keyboard([["❌ Cancel"]]),
            preserve_previous=True,
        )
        return UPDATE_MEDIA

    if stage == "banner":
        if text.lower() == "skip":
            bot_state.set_user(
                user_id,
                banner_file_id=None,
                update_stage="socials",
            )
        elif photo_file_id:
            bot_state.set_user(
                user_id,
                banner_file_id=photo_file_id,
                update_stage="socials",
            )
        else:
            await send_message(
                update,
                "Please send your <b>Project Banner</b> as an image, or type <b>'skip'</b>.",
                reply_markup=get_inline_keyboard([["❌ Cancel"]]),
                preserve_previous=True,
            )
            return UPDATE_MEDIA

        user = bot_state.get_user(user_id)
        await send_message(
            update,
            get_banner_received_message(skipped=not photo_file_id),
            reply_markup=get_inline_keyboard(
                get_social_media_buttons(user.get("socials"))
            ),
            preserve_previous=True,
        )
        return SOCIAL_LINKS

    return SOCIAL_LINKS

def _payment_record_inputs(user):
    service = user.get("service", "")
    blockchain = user.get("blockchain", "")
    tier = user.get("tier", "")
    amount, address = get_payment_details(
        service,
        blockchain,
        tier,
        wallet_address=user.get("wallet_address"),
    )
    currency = (
        amount.rsplit(" ", 1)[-1]
        if not amount.startswith("$")
        else CHAIN_CURRENCIES.get(blockchain, "")
    )
    expected_amount = parse_native_amount(amount, currency)
    project = user.get("project") or {}
    project_name = project.get("name")
    project_symbol = project.get("symbol")
    if project_name and project_symbol and project_name != project_symbol:
        token_name = f"{project_name} ({project_symbol})"
    else:
        token_name = project_name or project_symbol or user.get(
            "token_address",
            "Unknown",
        )
    return {
        "service": service,
        "platform": user.get("platform", "DexScreener"),
        "tier": tier,
        "blockchain": blockchain,
        "currency": currency,
        "token_address": user.get("token_address", ""),
        "token_name": token_name,
        "expected_amount": expected_amount,
        "expected_amount_text": amount,
        "recipient_address": address,
    }


async def _verify_payment_until_timeout(payment, transaction_hash):
    """Recheck pending transactions, never exceeding two minutes."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + 120
    for attempt in range(12):
        remaining = deadline - loop.time()
        if remaining <= 0:
            break
        record_verification_attempt(payment["id"])
        try:
            result = await asyncio.wait_for(
                verify_payment(payment, transaction_hash),
                timeout=remaining,
            )
        except asyncio.TimeoutError:
            break
        if result.status != "pending":
            return result
        if attempt < 11:
            remaining = deadline - loop.time()
            if remaining <= 0:
                break
            await asyncio.sleep(min(10, remaining))
    return VerificationResult(
        "timeout",
        "No confirmed transaction was found for this hash within two minutes.",
    )


def _payment_failure_message(result):
    if result.status == "unsupported":
        return (
            "Automatic verification is not configured for this "
            "blockchain or service yet."
        )
    if result.status == "rejected":
        return result.reason or "The transaction was rejected or did not match the payment."
    return "The transaction was not confirmed within the verification period."


def _display_service_name(service, tier):
    service_names = {
        "DexScreener Boost": "Token Boost",
        "DexScreener Trending": "Token Trending",
        "DexScreener Volume": "Token Volume",
        "DexScreener Update": "DexScreener Update",
        "Pump.fun Boost": "Pump.fun Token Boost",
        "Pump.fun Trending": "Pump.fun Trending",
        "Pump.fun Volume": "Pump.fun Volume Bot",
        "Pump.fun Graduation": "Pump.fun Graduation Boost",
    }
    return f"{service_names.get(service, service)} ({tier})"


async def _complete_payment_verification(
    update,
    user_id,
    payment_id,
    transaction_hash,
):
    """Verify in the background and send exactly one final result."""
    try:
        payment = get_payment(payment_id, user_id)
        if payment is None:
            return

        result = await _verify_payment_until_timeout(payment, transaction_hash)
        if result.status == "confirmed":
            mark_payment_confirmed(payment_id, transaction_hash)
            if not claim_fulfillment(payment_id):
                await send_message(
                    update,
                    "✅ <b>This payment was already processed.</b>\n\n"
                    "The transaction cannot be used for another order.",
                    reply_markup=ReplyKeyboardMarkup(
                        MAIN_MENU_BUTTONS,
                        resize_keyboard=True,
                    ),
                    preserve_previous=True,
                )
                bot_state.clear_user(user_id)
                return

            confirmed_payment = get_payment(payment_id, user_id)
            token_name = (
                confirmed_payment["token_name"]
                or confirmed_payment["token_address"]
            )
            await send_message(
                update,
                get_payment_verified_message(
                    order_id=confirmed_payment["id"],
                    service=_display_service_name(
                        confirmed_payment["service"],
                        confirmed_payment["tier"],
                    ),
                    platform=confirmed_payment["platform"],
                    amount=confirmed_payment["expected_amount_text"],
                    token_name=token_name,
                    transaction_hash=confirmed_payment["transaction_hash"],
                ),
                reply_markup=ReplyKeyboardMarkup(
                    MAIN_MENU_BUTTONS,
                    resize_keyboard=True,
                ),
                preserve_previous=True,
            )
            bot_state.clear_user(user_id)
            return

        failure_status = {
            "rejected": "rejected",
            "unsupported": "unsupported",
            "timeout": "timeout",
            "pending": "timeout",
        }.get(result.status, "not_received")
        failure_reason = _payment_failure_message(result)
        mark_payment_not_received(
            payment_id,
            failure_reason,
            status=failure_status,
        )
        await send_message(
            update,
            get_payment_not_received_message(failure_reason),
            reply_markup=get_inline_keyboard(get_payment_retry_buttons()),
            preserve_previous=True,
        )
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception(
            "Payment verification task failed for payment %s",
            payment_id,
        )
        try:
            payment = get_payment(payment_id, user_id)
            if payment and payment["status"] == "verifying":
                reason = "We could not complete the transaction check."
                mark_payment_not_received(
                    payment_id,
                    reason,
                    status="timeout",
                )
                await send_message(
                    update,
                    get_payment_not_received_message(reason),
                    reply_markup=get_inline_keyboard(get_payment_retry_buttons()),
                    preserve_previous=True,
                )
        except Exception:
            logger.exception(
                "Could not report failed payment verification for %s",
                payment_id,
            )
    finally:
        current_user = bot_state.get_user(user_id)
        if current_user.get("payment_id") == payment_id:
            bot_state.set_user(user_id, verification_task=None)


async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show payment instructions and require a transaction hash."""
    navigated_state = await handle_reply_keyboard_navigation(update, context)
    if navigated_state is not None:
        return navigated_state

    text = get_update_text(update)
    user_id = update.effective_user.id

    normalized_text = text.strip().casefold().replace("’", "'")
    if normalized_text in {
        "💰 i've paid",
        "i've paid",
        "💰 i have paid",
        "i have paid",
    }:
        user = bot_state.get_user(user_id)
        verification_task = user.get("verification_task")
        if verification_task and not verification_task.done():
            await send_message(
                update,
                get_payment_checking_message(),
                preserve_previous=True,
            )
            return TRANSACTION_HASH
        payment_id = user.get("payment_id")
        if payment_id is None:
            payment_data = _payment_record_inputs(user)
            if not payment_data["recipient_address"]:
                await send_message(
                    update,
                    "❌ <b>Payment wallet unavailable</b>\n\n"
                    "No payment wallet is assigned for this order yet.",
                    reply_markup=get_inline_keyboard(
                        [["🔙 Back to Token"], ["❌ Cancel"]]
                    ),
                )
                return PAYMENT
            try:
                payment_id = create_payment(
                    telegram_user_id=user_id,
                    **payment_data,
                )
            except Exception:
                logger.exception(
                    "Could not create payment record for Telegram user %s",
                    user_id,
                )
                await send_message(
                    update,
                    "❌ <b>Payment session unavailable</b>\n\n"
                    "We could not start payment verification right now. "
                    "Please try again in a moment or contact support.",
                    reply_markup=get_inline_keyboard(get_payment_buttons()),
                    preserve_previous=True,
                )
                return PAYMENT
            bot_state.set_user(user_id, payment_id=payment_id)

        await send_message(
            update,
            get_transaction_hash_message(user.get("blockchain", "")),
            reply_markup=get_inline_keyboard(get_transaction_hash_buttons()),
        )
        return TRANSACTION_HASH

    elif text == "🔙 Back to Token":
        user = bot_state.get_user(user_id)
        blockchain = user.get("blockchain")
        reply_keyboard = [["🔙 Back to Tiers"], ["❌ Cancel"]]
        markup = get_inline_keyboard(reply_keyboard)
        await send_message(update, get_token_address_message(blockchain), reply_markup=markup)
        return TOKEN_ADDRESS
    
    elif text == "❌ Cancel":
        bot_state.clear_user(user_id)
        reply_keyboard = MAIN_MENU_BUTTONS
        markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
        await send_message(update,
            "❌ <b>Order cancelled.</b>",
            reply_markup=markup,
        )
        return PLATFORM

    return PAYMENT


async def handle_transaction_hash(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Claim, verify, and record the user's transaction hash."""
    navigated_state = await handle_reply_keyboard_navigation(update, context)
    if navigated_state is not None:
        return navigated_state

    text = get_update_text(update).strip()
    user_id = update.effective_user.id
    user = bot_state.get_user(user_id)
    payment_id = user.get("payment_id")

    if text == "🔙 Back to Payment":
        payment_data = _payment_record_inputs(user)
        await send_message(
            update,
            get_payment_message(
                payment_data["service"].replace("DexScreener ", ""),
                payment_data["platform"],
                payment_data["tier"],
                payment_data["token_name"],
                payment_data["expected_amount_text"],
                payment_data["recipient_address"],
                project_name=(
                    (user.get("project") or {}).get("name")
                    if user.get("project")
                    else None
                ),
            ),
            reply_markup=get_inline_keyboard(get_payment_buttons()),
        )
        return PAYMENT

    if text == "🔄 Try Another Transaction Hash":
        await send_message(
            update,
            get_transaction_hash_message(user.get("blockchain", "")),
            reply_markup=get_inline_keyboard(get_transaction_hash_buttons()),
        )
        return TRANSACTION_HASH

    if text == "❌ Cancel":
        bot_state.clear_user(user_id)
        await send_message(
            update,
            "❌ <b>Order cancelled.</b>",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True),
        )
        return PLATFORM

    if not payment_id or not text:
        await send_message(
            update,
            get_transaction_hash_message(user.get("blockchain", "")),
            reply_markup=get_inline_keyboard(get_transaction_hash_buttons()),
        )
        return TRANSACTION_HASH

    # Preserve the complete order history after the first hash is submitted.
    bot_state.set_user(user_id, preserve_chat_history=True)
    payment = get_payment(payment_id, user_id)
    if payment is None:
        await send_message(
            update,
            "❌ <b>Payment order unavailable</b>\n\nPlease start the order again.",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True),
        )
        bot_state.clear_user(user_id)
        return PLATFORM

    transaction_hash = normalize_transaction_hash(
        payment["blockchain"],
        text,
    )
    try:
        payment = claim_transaction(payment_id, user_id, transaction_hash)
    except DuplicateTransactionError:
        await send_message(
            update,
            get_payment_not_received_message(
                "This transaction has already been used for a payment."
            ),
            reply_markup=get_inline_keyboard(get_payment_retry_buttons()),
            preserve_previous=True,
        )
        return TRANSACTION_HASH
    except PaymentStateError as error:
        if str(error) == "This payment is already being verified.":
            await send_message(
                update,
                get_payment_checking_message(),
                preserve_previous=True,
            )
            return TRANSACTION_HASH
        await send_message(
            update,
            get_payment_not_received_message(str(error)),
            reply_markup=get_inline_keyboard(get_payment_retry_buttons()),
            preserve_previous=True,
        )
        return TRANSACTION_HASH

    await send_message(
        update,
        get_payment_checking_message(),
        preserve_previous=True,
    )
    verification_task = context.application.create_task(
        _complete_payment_verification(
            update,
            user_id,
            payment_id,
            transaction_hash,
        ),
        update=update,
    )
    bot_state.set_user(user_id, verification_task=verification_task)
    return TRANSACTION_HASH


async def handle_social_links(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle social media links for Update service"""
    navigated_state = await handle_reply_keyboard_navigation(update, context)
    if navigated_state is not None:
        return navigated_state

    text = get_update_text(update)
    user_id = update.effective_user.id

    if text == "❌ Cancel":
        bot_state.clear_user(user_id)
        await send_message(
            update,
            "❌ <b>Cancelled.</b>\n\nBack to the main menu.",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True),
        )
        return PLATFORM

    if text == "✅ Submit Media & Links":
        user = bot_state.get_user(user_id)
        await send_message(
            update,
            get_update_confirmation_message(
                user.get("project"),
                user.get("token_address", ""),
                bool(user.get("logo_file_id")),
                bool(user.get("banner_file_id")),
                user.get("socials") or {},
            ),
            reply_markup=get_inline_keyboard(get_update_confirmation_buttons()),
            preserve_previous=True,
        )
        return TOKEN_CONFIRMATION

    social_button_names = {
        "Add Telegram": "Telegram",
        "Add Twitter": "Twitter",
        "Add Discord": "Discord",
        "Add Website": "Website",
        "[ADDED] Telegram": "Telegram",
        "[ADDED] Twitter": "Twitter",
        "[ADDED] Discord": "Discord",
        "[ADDED] Website": "Website",
    }
    if text in social_button_names:
        social_name = social_button_names[text]
        bot_state.set_user(user_id, pending_social=social_name)
        await send_message(
            update,
            f"📝 <b>Add {social_name} link</b>\n\n"
            "Please send the complete link in your next message.",
            reply_markup=get_inline_keyboard([["❌ Cancel"]]),
            preserve_previous=True,
        )
        return SOCIAL_LINKS

    user = bot_state.get_user(user_id)
    pending_social = user.get("pending_social")
    if pending_social and text.strip():
        socials = dict(user.get("socials") or {})
        socials[pending_social] = text.strip()
        bot_state.set_user(
            user_id,
            socials=socials,
            pending_social=None,
        )
        await send_message(
            update,
            get_social_links_message(),
            reply_markup=get_inline_keyboard(get_social_media_buttons(socials)),
            preserve_previous=True,
        )
        return SOCIAL_LINKS

    await send_message(
        update,
        get_social_links_message(),
        reply_markup=get_inline_keyboard(
            get_social_media_buttons(user.get("socials"))
        ),
        preserve_previous=True,
    )
    return SOCIAL_LINKS

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel conversation"""
    user_id = update.effective_user.id
    bot_state.clear_user(user_id)
    reply_keyboard = MAIN_MENU_BUTTONS
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "❌ <b>Cancelled.</b>\n\nBack to the main menu.",
        reply_markup=markup,
    )
    return PLATFORM

def main():
    """Start the bot"""
    # Check if token is set
    if not TELEGRAM_BOT_TOKEN:
        logger.error(
            "TELEGRAM_BOT_TOKEN is not configured. Add it to Replit Secrets "
            "before starting the bot."
        )
        return
    
    # Create application
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .defaults(Defaults(parse_mode=ParseMode.HTML))
        .build()
    )

    # Observe all incoming Telegram activity before the conversation handlers.
    # The configured owner/admin IDs are excluded by activity_notifications.
    application.add_handler(
        TypeHandler(Update, blocked_user_handler),
        group=-2,
    )
    application.add_handler(
        TypeHandler(Update, activity_notification_handler),
        group=-1,
    )
    application.add_handler(
        CommandHandler("admin", admin_panel),
        group=-1,
    )
    application.add_handler(
        CommandHandler("ban", admin_ban_command),
        group=-1,
    )
    application.add_handler(
        CommandHandler("unban", admin_unban_command),
        group=-1,
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_admin_callback,
            pattern=r"^admin:(ban|unban|list)$",
        ),
        group=-1,
    )
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_pending_admin_text,
        ),
        group=-1,
    )
    
    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        allow_reentry=True,
        states={
            PLATFORM: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_platform)],
            SERVICE: [
                CallbackQueryHandler(handle_service),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_service),
            ],
            BLOCKCHAIN: [
                CallbackQueryHandler(handle_blockchain),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_blockchain),
            ],
            TIER: [
                CallbackQueryHandler(handle_tier),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tier),
            ],
            TOKEN_ADDRESS: [
                CallbackQueryHandler(handle_token_address),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_token_address),
            ],
            TOKEN_CONFIRMATION: [
                CallbackQueryHandler(handle_token_confirmation),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_token_confirmation),
            ],
            UPDATE_MEDIA: [
                CallbackQueryHandler(handle_update_media),
                MessageHandler(
                    filters.PHOTO | filters.Document.ALL,
                    handle_update_media,
                ),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_update_media),
            ],
            PAYMENT: [
                CallbackQueryHandler(handle_payment),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_payment),
            ],
            TRANSACTION_HASH: [
                CallbackQueryHandler(handle_transaction_hash),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_transaction_hash),
            ],
            SOCIAL_LINKS: [
                CallbackQueryHandler(handle_social_links),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_social_links),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(conv_handler)

    admin_thread = threading.Thread(
        target=start_admin_server,
        name="wallet-admin",
        daemon=True,
    )
    admin_thread.start()
    
    logger.info("DEX Telegram bot is starting polling.")
    application.run_polling()

if __name__ == '__main__':
    main()
