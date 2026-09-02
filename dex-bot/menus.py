# Menu messages and keyboard layouts
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import BLOCKCHAINS
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


def get_inline_keyboard(button_rows):
    """Build buttons that appear directly below a Telegram message."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(label, callback_data=label)
                for label in row
            ]
            for row in button_rows
        ]
    )


# Main menu message
def get_main_menu():
    return """<b>DexScreener Services</b>

Please select a service:"""


def get_pumpfun_services_message():
    return """<b>Pump.fun Services</b>

Please select a service:"""


def get_four_meme_services_message():
    return """<b>Four.Meme Services</b>

Please select a service:"""


def get_flapsh_services_message():
    return """<b>Flap.sh Services</b>

Please select a service:"""


# Service descriptions
def get_service_message(service_name):
    messages = {
        "DexScreener Update": (
            "<b>DexScreener Update Selected</b>\n\n"
            "Update your Token Info, Logo, Banner, and Socials\n\n"
            "Please select the blockchain where your token is deployed:"
        ),
        "DexScreener Trending": (
            "<b>Trending Service Selected</b>\n\n"
            "Get your token in trending lists\n\n"
            "Please select the blockchain where your token is deployed:"
        ),
        "DexScreener Volume": (
            "<b>Volume Bot Selected</b>\n\n"
            "Increase apparent trading volume\n\n"
            "Please select the blockchain where your token is deployed:"
        ),
        "DexScreener Boost": (
            "<b>Token Boost Selected</b>\n\n"
            "Increase your token's visibility on DexScreener\n\n"
            "Please select the blockchain where your token is deployed:"
        ),
        "Pump.fun Boost": (
            "<b>Pump.fun Token Boost Selected</b>\n\n"
            "Boost your Pump.fun token with volume and holder activity\n\n"
            "<b>Platform:</b> Pump.fun (Solana)\n\n"
            "<b>Select Tier:</b>\n\n"
            "1. <b>Basic Pump</b> - Light volume and holder increase\n"
            "   <b>Price: 0.5000 SOL</b>\n\n"
            "2. <b>Medium Pump</b> - Moderate volume and holder boost\n"
            "   <b>Price: 1.0000 SOL</b>\n\n"
            "3. <b>Mega Pump</b> - Heavy volume and maximum holder boost\n"
            "   <b>Price: 2.0000 SOL</b>\n\n"
            "👇 <i>Select a Pump.fun Boost tier below.</i>"
        ),
        "Pump.fun Trending": (
            "<b>Pump.fun Trending Selected</b>\n\n"
            "Get your token trending on Pump.fun\n\n"
            "<b>Platform:</b> Pump.fun (Solana)\n\n"
            "<b>Select Tier:</b>\n\n"
            "1. <b>Trending Basic</b> - Basic trending placement\n"
            "   <b>Price: 1.0000 SOL</b>\n\n"
            "2. <b>Trending Advanced</b> - Higher trending position\n"
            "   <b>Price: 1.8000 SOL</b>\n\n"
            "3. <b>Trending Premium</b> - Top trending spots\n"
            "   <b>Price: 3.0000 SOL</b>\n\n"
            "👇 <i>Select a Pump.fun Trending tier below.</i>"
        ),
        "Pump.fun Volume": (
            "<b>Pump.fun Volume Bot Selected</b>\n\n"
            "Generate consistent on-chain trading volume\n\n"
            "<b>Platform:</b> Pump.fun (Solana)\n\n"
            "<b>Select Tier:</b>\n\n"
            "1. <b>50K Volume</b> - Generate 50k trading volume\n"
            "   <b>Price: 1.5000 SOL</b>\n\n"
            "2. <b>100K Volume</b> - Generate 100k trading volume\n"
            "   <b>Price: 3.0000 SOL</b>\n\n"
            "3. <b>250K Volume</b> - Generate 250k trading volume\n"
            "   <b>Price: 7.5000 SOL</b>\n\n"
            "4. <b>500K Volume</b> - Generate 500k trading volume\n"
            "   <b>Price: 15.0000 SOL</b>\n\n"
            "5. <b>750K Volume</b> - Generate 750k trading volume\n"
            "   <b>Price: 22.5000 SOL</b>\n\n"
            "6. <b>1M Volume</b> - Generate 1M trading volume\n"
            "   <b>Price: 30.0000 SOL</b>\n\n"
            "7. <b>5M Volume</b> - Generate 5M trading volume\n"
            "   <b>Price: 150.0000 SOL</b>\n\n"
            "👇 <i>Select a Pump.fun Volume tier below.</i>"
        ),
        "Pump.fun Graduation": (
            "<b>Pump.fun Graduation Boost Selected</b>\n\n"
            "Help your token reach graduation faster\n\n"
            "<b>Platform:</b> Pump.fun (Solana)\n\n"
            "<b>Select Tier:</b>\n\n"
            "1. <b>Graduation Assist</b> - Moderate push towards graduation\n"
            "   <b>Price: 2.5000 SOL</b>\n\n"
            "2. <b>Graduation Boost</b> - Strong push with volume burst\n"
            "   <b>Price: 4.0000 SOL</b>\n\n"
            "3. <b>Graduation Express</b> - Maximum graduation assistance\n"
            "   <b>Price: 6.0000 SOL</b>\n\n"
            "👇 <i>Select a Pump.fun Graduation tier below.</i>"
        ),
        "Four.Meme Boost": (
            "<b>Four.Meme Token Boost Selected</b>\n\n"
            "Boost your Four.Meme BSC token with volume and holder activity\n\n"
            "<b>Platform:</b> Four.Meme (BSC)\n\n"
            "<b>Select Tier:</b>\n\n"
            "1. <b>Basic Pump</b> - Light volume and holder increase\n"
            "   <b>Price: 0.3000 BNB</b>\n\n"
            "2. <b>Medium Pump</b> - Moderate volume and holder boost\n"
            "   <b>Price: 0.6000 BNB</b>\n\n"
            "3. <b>Mega Pump</b> - Heavy volume and maximum holder boost\n"
            "   <b>Price: 1.0000 BNB</b>\n\n"
            "👇 <i>Select a Four.Meme Boost tier below.</i>"
        ),
        "Four.Meme Trending": (
            "<b>Four.Meme Trending Selected</b>\n\n"
            "Get your token trending on Four.Meme\n\n"
            "<b>Platform:</b> Four.Meme (BSC)\n\n"
            "<b>Select Tier:</b>\n\n"
            "1. <b>Trending Basic</b> - Basic Four.Meme trending placement\n"
            "   <b>Price: 0.0640 BNB</b>\n\n"
            "2. <b>Trending Advanced</b> - Higher trending position\n"
            "   <b>Price: 0.1280 BNB</b>\n\n"
            "3. <b>Trending Premium</b> - Top trending spots on Four.Meme\n"
            "   <b>Price: 0.2560 BNB</b>\n\n"
            "👇 <i>Select a Four.Meme Trending tier below.</i>"
        ),
        "Four.Meme Volume": (
            "<b>Four.Meme Volume Bot Selected</b>\n\n"
            "Generate consistent on-chain trading volume\n\n"
            "<b>Platform:</b> Four.Meme (BSC)\n\n"
            "<b>Select Tier:</b>\n\n"
            "1. <b>50K Volume</b> - Generate 50K trading volume\n"
            "   <b>Price: 0.3840 BNB</b>\n\n"
            "2. <b>100K Volume</b> - Generate 100K trading volume\n"
            "   <b>Price: 0.7680 BNB</b>\n\n"
            "3. <b>250K Volume</b> - Generate 250K trading volume\n"
            "   <b>Price: 1.9200 BNB</b>\n\n"
            "4. <b>500K Volume</b> - Generate 500K trading volume\n"
            "   <b>Price: 3.8400 BNB</b>\n\n"
            "5. <b>750K Volume</b> - Generate 750K trading volume\n"
            "   <b>Price: 5.7600 BNB</b>\n\n"
            "6. <b>1M Volume</b> - Generate 1M trading volume\n"
            "   <b>Price: 7.6800 BNB</b>\n\n"
            "7. <b>5M Volume</b> - Generate 5M trading volume\n"
            "   <b>Price: 38.4000 BNB</b>\n\n"
            "👇 <i>Select a Four.Meme Volume tier below.</i>"
        ),
        "Flap.sh Boost": (
            "<b>Flap.sh Token Boost Selected</b>\n\n"
            "Boost your Flap.sh BSC token with volume and holder activity\n\n"
            "<b>Platform:</b> Flap.sh (BSC)\n\n"
            "<b>Select Tier:</b>\n\n"
            "1. <b>Basic Pump</b> - Light volume and holder increase\n"
            "   <b>Price: 0.3000 BNB</b>\n\n"
            "2. <b>Medium Pump</b> - Moderate volume and holder boost\n"
            "   <b>Price: 0.6000 BNB</b>\n\n"
            "3. <b>Mega Pump</b> - Heavy volume and maximum holder boost\n"
            "   <b>Price: 1.0000 BNB</b>\n\n"
            "👇 <i>Select a Flap.sh Boost tier below.</i>"
        ),
        "Flap.sh Trending": (
            "<b>Flap.sh Trending Selected</b>\n\n"
            "Get your token trending on Flap.sh\n\n"
            "<b>Platform:</b> Flap.sh (BSC)\n\n"
            "<b>Select Tier:</b>\n\n"
            "1. <b>Trending Basic</b> - Basic Flap.sh trending placement\n"
            "   <b>Price: 0.0640 BNB</b>\n\n"
            "2. <b>Trending Advanced</b> - Higher trending position\n"
            "   <b>Price: 0.1280 BNB</b>\n\n"
            "3. <b>Trending Premium</b> - Top trending spots on Flap.sh\n"
            "   <b>Price: 0.2560 BNB</b>\n\n"
            "👇 <i>Select a Flap.sh Trending tier below.</i>"
        ),
        "Flap.sh Volume": (
            "<b>Flap.sh Volume Bot Selected</b>\n\n"
            "Generate consistent on-chain trading volume\n\n"
            "<b>Platform:</b> Flap.sh (BSC)\n\n"
            "<b>Select Tier:</b>\n\n"
            "1. <b>50K Volume</b> - Generate 50K trading volume\n"
            "   <b>Price: 0.3840 BNB</b>\n\n"
            "2. <b>100K Volume</b> - Generate 100K trading volume\n"
            "   <b>Price: 0.7680 BNB</b>\n\n"
            "3. <b>250K Volume</b> - Generate 250K trading volume\n"
            "   <b>Price: 1.9200 BNB</b>\n\n"
            "4. <b>500K Volume</b> - Generate 500K trading volume\n"
            "   <b>Price: 3.8400 BNB</b>\n\n"
            "5. <b>750K Volume</b> - Generate 750K trading volume\n"
            "   <b>Price: 5.7600 BNB</b>\n\n"
            "6. <b>1M Volume</b> - Generate 1M trading volume\n"
            "   <b>Price: 7.6800 BNB</b>\n\n"
            "7. <b>5M Volume</b> - Generate 5M trading volume\n"
            "   <b>Price: 38.4000 BNB</b>\n\n"
            "👇 <i>Select a Flap.sh Volume tier below.</i>"
        ),
    }
    return messages.get(service_name, "Service selected")


# Tier selection messages
def get_update_tier_message():
    update_pricing = DEXSCREENER_UPDATE_PRICING["all_chains"]
    return """<b>Choose an Update Tier</b>

1. <b>CTO Update</b>
   Community takeover information update
   <b>Price: {cto_price}</b>

2. <b>Token Info Update</b>
   Full DexScreener information update
   <b>Price: {token_info_price}</b>

👇 <i>Select a tier below.</i>""".format(
        cto_price=update_pricing["CTO Update"]["price"],
        token_info_price=update_pricing["Token Info Update"]["price"],
    )


def get_trending_tier_message(blockchain):
    pricing = DEXSCREENER_TRENDING_PRICING.get(blockchain, {})
    return f"""<b>{blockchain} Trending Service</b>

1. <b>Basic</b>
   Regular trending placement
   <b>Price: {pricing.get("Basic", {}).get("price", "Not configured")}</b>

2. <b>Advanced</b>
   Higher trending positions
   <b>Price: {pricing.get("Advanced", {}).get("price", "Not configured")}</b>

3. <b>Premium</b>
   Top trending placements
   <b>Price: {pricing.get("Premium", {}).get("price", "Not configured")}</b>

👇 <i>Select a tier below.</i>"""


def get_volume_tier_message(blockchain):
    pricing = DEXSCREENER_VOLUME_PRICING.get(blockchain, {})
    lines = [f"<b>{blockchain} Volume Bot</b>", ""]
    for number, (tier, details) in enumerate(pricing.items(), start=1):
        lines.extend(
            [
                f"{number}. <b>{tier} Volume</b>",
                f"   {details['description']}",
                f"   <b>Price: {details['price']}</b>",
                "",
            ]
        )
    lines.append("👇 <i>Select a Volume Bot tier below.</i>")
    return "\n".join(lines)


def get_boost_tier_message(blockchain):
    pricing = DEXSCREENER_BOOST_PRICING.get(blockchain, {})
    lines = [f"<b>{blockchain} Token Boost</b>", ""]
    for number, (tier, details) in enumerate(pricing.items(), start=1):
        lines.extend(
            [
                f"{number}. <b>{tier}</b>",
                f"   {details['description']}",
                f"   <b>Price: {details['price']}</b>",
                "",
            ]
        )
    lines.append("👇 <i>Select a Token Boost tier below.</i>")
    return "\n".join(lines)


def get_boost_pricing_menu_messages():
    sections = []
    for blockchain, pricing in DEXSCREENER_BOOST_PRICING.items():
        section = [f"<b>{blockchain}</b>", "Select Boost tier:"]
        for number, (tier, details) in enumerate(pricing.items(), start=1):
            section.append(
                f"{number}. <b>{tier} Boost</b> - "
                f"{details['description']} "
                f"<b>Price: {details['price']}</b>"
            )
        sections.append("\n".join(section))

    messages = ["<b>DexScreener Boost Pricing</b>"]
    for section in sections:
        candidate = f"{messages[-1]}\n\n{section}"
        if len(candidate) > 3500:
            messages.append(section)
        else:
            messages[-1] = candidate
    messages[-1] += "\n\n👇 <i>Select a blockchain below to place an order.</i>"
    return messages


def get_boost_pricing_menu_message():
    """Return the complete write-up for tests and non-Telegram consumers."""
    return "\n\n".join(get_boost_pricing_menu_messages())


# Token address input
def get_token_address_message(blockchain):
    return f"""<b>Enter Token Address</b>

Please enter your <b>{blockchain}</b> token contract address:"""


# Token verification
def get_token_verification_message():
    return """🔍 <b>Verifying token</b>

Please wait while we look up the token across public metadata sources..."""


def _format_price(value):
    if value in (None, ""):
        return "Unavailable"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number == 0:
        return "$0"
    if number < 0.0001:
        return f"${number:.10f}".rstrip("0").rstrip(".")
    if number < 1:
        return f"${number:.8f}".rstrip("0").rstrip(".")
    return f"${number:,.4f}".rstrip("0").rstrip(".")


def _format_volume(value):
    if value in (None, ""):
        return "Unavailable"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number >= 1_000_000:
        return f"${number / 1_000_000:.2f}M"
    if number >= 1_000:
        return f"${number / 1_000:.2f}K"
    return f"${number:,.2f}"


def _format_market_cap(value):
    if value in (None, ""):
        return "Unavailable"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number >= 1_000_000_000:
        return f"${number / 1_000_000_000:.2f}B"
    if number >= 1_000_000:
        return f"${number / 1_000_000:.2f}M"
    if number >= 1_000:
        return f"${number / 1_000:.2f}K"
    return f"${number:,.2f}"


def get_pumpfun_boost_tier_buttons():
    return [
        ["Basic Pump (0.5000 SOL)", "Medium Pump (1.0000 SOL)"],
        ["Mega Pump (2.0000 SOL)"],
        ["🔙 Back to Main Menu"],
    ]


def get_pumpfun_trending_tier_buttons():
    return [
        ["Trending Basic (1.0000 SOL)", "Trending Advanced (1.8000 SOL)"],
        ["Trending Premium (3.0000 SOL)"],
        ["🔙 Back to Main Menu"],
    ]


def get_pumpfun_volume_tier_buttons():
    return [
        ["50K Volume (1.5000 SOL)", "100K Volume (3.0000 SOL)"],
        ["250K Volume (7.5000 SOL)", "500K Volume (15.0000 SOL)"],
        ["750K Volume (22.5000 SOL)", "1M Volume (30.0000 SOL)"],
        ["5M Volume (150.0000 SOL)"],
        ["🔙 Back to Main Menu"],
    ]


def get_pumpfun_graduation_tier_buttons():
    return [
        ["Graduation Assist (2.5000 SOL)", "Graduation Boost (4.0000 SOL)"],
        ["Graduation Express (6.0000 SOL)"],
        ["🔙 Back to Main Menu"],
    ]


def get_four_meme_boost_tier_buttons():
    return [
        ["Basic Pump (0.3000 BNB)", "Medium Pump (0.6000 BNB)"],
        ["Mega Pump (1.0000 BNB)"],
        ["🔙 Back to Main Menu"],
    ]


def get_four_meme_trending_tier_buttons():
    return [
        ["Trending Basic (0.0640 BNB)", "Trending Advanced (0.1280 BNB)"],
        ["Trending Premium (0.2560 BNB)"],
        ["🔙 Back to Main Menu"],
    ]


def get_four_meme_volume_tier_buttons():
    return [
        ["50K Volume (0.3840 BNB)", "100K Volume (0.7680 BNB)"],
        ["250K Volume (1.9200 BNB)", "500K Volume (3.8400 BNB)"],
        ["750K Volume (5.7600 BNB)", "1M Volume (7.6800 BNB)"],
        ["5M Volume (38.4000 BNB)"],
        ["🔙 Back to Main Menu"],
    ]


def get_flapsh_boost_tier_buttons():
    return [
        ["Basic Pump (0.3000 BNB)", "Medium Pump (0.6000 BNB)"],
        ["Mega Pump (1.0000 BNB)"],
        ["🔙 Back to Main Menu"],
    ]


def get_flapsh_trending_tier_buttons():
    return [
        ["Trending Basic (0.0640 BNB)", "Trending Advanced (0.1280 BNB)"],
        ["Trending Premium (0.2560 BNB)"],
        ["🔙 Back to Main Menu"],
    ]


def get_flapsh_volume_tier_buttons():
    return [
        ["50K Volume (0.3840 BNB)", "100K Volume (0.7680 BNB)"],
        ["250K Volume (1.9200 BNB)", "500K Volume (3.8400 BNB)"],
        ["750K Volume (5.7600 BNB)", "1M Volume (7.6800 BNB)"],
        ["5M Volume (38.4000 BNB)"],
        ["🔙 Back to Main Menu"],
    ]


def get_pumpfun_token_info_message(project, contract_address):
    """Format the Pump.fun token card shown before confirmation."""
    from html import escape

    project = project or {}
    name = project.get("name") or "Unavailable"
    symbol = project.get("symbol") or "Unavailable"
    return f"""<b>Pump.fun Token Information:</b>

<b>Name:</b> {escape(name)} ({escape(symbol)})
<b>Symbol:</b> {escape(symbol)}
<b>Address:</b>
<code>{escape(contract_address)}</code>
<b>Market Cap:</b> {_format_market_cap(project.get("market_cap_usd"))}
<b>Platform:</b> Pump.fun"""


def get_pumpfun_token_confirmation_message(service="Pump.fun Boost"):
    actions = {
        "Pump.fun Boost": "boost",
        "Pump.fun Trending": "place in Pump.fun Trending",
        "Pump.fun Volume": "use for Pump.fun Volume",
        "Pump.fun Graduation": "use for Pump.fun Graduation",
    }
    action = actions.get(service, "use for this Pump.fun service")
    return f"""Is this the correct token you want to {action}?

Please confirm:"""


def get_update_token_info_message(project, blockchain, contract_address):
    """Format the token card shown before the Update media collection."""
    from html import escape

    project = project or {}
    return f"""<b>DexScreener Token Information:</b>

<b>Name:</b> {escape(project.get("name") or "Unavailable")}
<b>Symbol:</b> {escape(project.get("symbol") or "Unavailable")}
<b>Address:</b>
<code>{escape(contract_address)}</code>
<b>Price:</b> {_format_price(project.get("price_usd"))}
<b>24h Volume:</b> {_format_volume(project.get("volume_24h"))}
<b>Exchange:</b> {escape(project.get("exchange") or "Unavailable")}"""


def get_update_logo_prompt():
    return """📝 <b>Token Verified for DexScreener Update</b>

To begin the update process, please send an <b>image of your Project Logo</b> directly to this chat:"""


def get_logo_received_message():
    return """🖼 <b>Logo Received</b>

Now, please send an <b>image of your Project Banner</b> to this chat.
(or type <b>'skip'</b> if you don't have one):"""


def get_banner_received_message(skipped=False):
    heading = "Banner Skipped" if skipped else "Banner Received"
    return f"""✅ <b>{heading}</b>

Lastly, please provide your <b>Social Links</b> by clicking the buttons below.
Once you are done, click <b>'Submit Media &amp; Links'</b>:"""


def get_update_confirmation_message(project, contract_address, logo_uploaded, banner_uploaded, socials):
    from html import escape

    project = project or {}
    name = project.get("name") or "Unavailable"
    symbol = project.get("symbol") or name
    social_lines = [
        f"• <b>{escape(name)}:</b> {escape(value)}"
        for name, value in (socials or {}).items()
    ]
    provided_socials = "\n".join(social_lines) if social_lines else "None"
    return f"""<b>DexScreener Update Information:</b>

<b>Token:</b> {escape(name)} ({escape(symbol)})
<b>Address:</b>
<code>{escape(contract_address)}</code>

<b>Logo Uploaded:</b> {'✅ Yes' if logo_uploaded else '❌ No'}
<b>Banner Uploaded:</b> {'✅ Yes' if banner_uploaded else '❌ No'}
<b>Provided Socials:</b>
{provided_socials}

Are these details correct for the DexScreener Update?
Please confirm to proceed to payment."""


def get_update_confirmation_buttons():
    return [
        ["Confirm Token"],
        ["Enter Different Address"],
        ["Back to Tiers"],
        ["❌ Cancel"],
    ]


def get_project_info_message(project, blockchain, contract_address):
    from html import escape

    if not project:
        return f"""🔎 <b>Project Information</b>

<b>Project:</b> Public metadata not found
<b>Network:</b> {escape(blockchain)}
<b>Contract:</b> <code>{escape(contract_address)}</code>"""

    lines = [
        "🔎 <b>Project Information</b>",
        "",
        f"<b>Name:</b> {escape(project['name'])}",
    ]
    if project.get("symbol"):
        lines.append(f"<b>Symbol:</b> {escape(project['symbol'])}")
    lines.extend(
        [
            f"<b>Network:</b> {escape(blockchain)}",
            f"<b>Contract:</b> <code>{escape(contract_address)}</code>",
        ]
    )
    if project.get("author"):
        lines.append(f"<b>Author:</b> {escape(project['author'])}")
    if project.get("source"):
        lines.append(f"<b>Metadata source:</b> {escape(project['source'])}")
    if project.get("pair_url"):
        lines.append(
            f'<b>DexScreener:</b> <a href="{escape(project["pair_url"])}">View pair</a>'
        )
    return "\n".join(lines)


def get_token_confirmation_message(project, blockchain, contract_address):
    from html import escape

    project_name = project.get("name") if project else None
    if project_name:
        return (
            f"<b>Is {escape(project_name)} the correct token you want to boost?</b>\n\n"
            "Please confirm:"
        )
    return (
        "<b>Is this the correct token you want to boost?</b>\n\n"
        f"<b>Network:</b> {escape(blockchain)}\n"
        f"<b>Contract:</b> <code>{escape(contract_address)}</code>\n\n"
        "Public metadata sources could not find a name or symbol for this address.\n"
        "You can still review and confirm the contract manually.\n\n"
        "Please confirm:"
    )


def get_token_confirmation_buttons():
    return [
        ["✅ Confirm Token"],
        ["🔄 Enter Different Address"],
        ["🔙 Back to Tiers"],
        ["❌ Cancel"],
    ]


# Order summary and payment
def get_payment_message(
    service,
    platform,
    tier,
    token_name,
    amount,
    address,
    project_name=None,
):
    from html import escape

    project_line = (
        f"<b>Project:</b> {escape(project_name)}\n"
        if project_name
        else ""
    )

    return f"""<b>📋 Order Summary</b>

<b>Service:</b> {escape(service)}
<b>Platform:</b> {escape(platform)}
<b>Tier:</b> {escape(tier)}
{project_line}<b>Contract:</b> {escape(token_name)}

💰 <b>Payment Details</b>

<b>Amount:</b> {escape(amount)}
<b>Wallet:</b>
<code>{escape(address)}</code>

⚠️ <b>Important:</b> Use the correct network and send exactly the amount shown above.

Click <b>“I've Paid”</b> below when complete."""


# Social links (for Update service)
def get_social_links_message():
    return """✅ <b>Banner Received</b>

Lastly, please provide your <b>Social Links</b> by clicking the buttons below.
Once you are done, click <b>'Submit Media &amp; Links'</b>:"""


# Button layouts
def get_blockchain_buttons():
    return [
        ["Ethereum", "Robinhood"],
        ["BNB Chain", "Polygon"],
        ["Arbitrum", "Avalanche"],
        ["Fantom", "Solana"],
        ["Base", "Cronos"],
        ["Kava", "TRON"],
        ["TON", "SUI"],
        ["🔙 Back to Services"],
    ]


def get_update_tier_buttons():
    return [
        ["CTO Update ($199)", "Token Info Update ($299)"],
        ["🔙 Back to Blockchain"],
    ]


def get_trending_tier_buttons(blockchain):
    """Show Trending tier buttons with the selected chain's prices."""
    pricing = DEXSCREENER_TRENDING_PRICING.get(blockchain, {})

    def tier_label(tier):
        price = pricing.get(tier, {}).get("price", "Price unavailable")
        return f"{tier} ({price})"

    return [
        [tier_label("Basic"), tier_label("Advanced")],
        [tier_label("Premium")],
        ["🔙 Back"],
    ]


def get_volume_tier_buttons(blockchain):
    pricing = DEXSCREENER_VOLUME_PRICING.get(blockchain, {})

    def tier_label(tier):
        price = pricing.get(tier, {}).get("price", "Price not configured")
        return f"{tier} ({price})"

    return [
        [tier_label("50K"), tier_label("100K")],
        [tier_label("250K"), tier_label("500K")],
        [tier_label("750K"), tier_label("1M")],
        [tier_label("5M")],
        ["🔙 Back"],
    ]


def get_boost_tier_buttons(blockchain):
    pricing = DEXSCREENER_BOOST_PRICING.get(blockchain, {})

    def tier_label(tier):
        price = pricing.get(tier, {}).get("price", "Price unavailable")
        return f"{tier} ({price})"

    tiers = list(pricing)
    rows = [
        [tier_label(tier) for tier in tiers[index:index + 2]]
        for index in range(0, max(len(tiers) - 1, 0), 2)
    ]
    if tiers:
        rows.append([tier_label(tiers[-1])])
    rows.append(["🔙 Back"])
    return rows


def get_boost_blockchain_buttons():
    blockchains = [
        blockchain
        for blockchain in BLOCKCHAINS
        if blockchain in DEXSCREENER_BOOST_PRICING
    ]
    rows = [
        blockchains[index:index + 2]
        for index in range(0, len(blockchains), 2)
    ]
    rows.append(["🔙 Back to Services"])
    return rows


def get_boost_quote_pending_message(project_name=None):
    project_line = (
        f"<b>Project:</b> {project_name}\n" if project_name else ""
    )
    return f"""✅ <b>Boost request ready</b>

{project_line}<b>Package:</b> DexScreener Boost

Your token has been verified and your Boost request is ready for pricing.
Final Boost rates are being added now. <b>Please do not send payment yet.</b>

Send us the confirmed pricing to activate payment for this package."""


def get_social_media_buttons(socials=None):
    socials = socials or {}
    return [
        [
            "[ADDED] Telegram" if socials.get("Telegram") else "Add Telegram",
            "[ADDED] Twitter" if socials.get("Twitter") else "Add Twitter",
        ],
        [
            "[ADDED] Discord" if socials.get("Discord") else "Add Discord",
            "[ADDED] Website" if socials.get("Website") else "Add Website",
        ],
        ["✅ Submit Media & Links"],
        ["❌ Cancel"],
    ]


def get_payment_buttons():
    return [["💰 I've Paid"], ["🔙 Back to Token"], ["❌ Cancel"]]


def get_transaction_hash_message(blockchain):
    from html import escape

    return f"""🔐 <b>Transaction Hash Required</b>

Please enter your transaction hash to verify the payment.

You can find this in your wallet or blockchain explorer after sending the payment.

💡 <b>Blockchain:</b> {escape(blockchain)}"""


def get_transaction_hash_buttons():
    return [["🔙 Back to Payment"], ["❌ Cancel"]]


def get_payment_checking_message():
    return """🔍 <b>Checking Payment</b>

Your transaction is being checked on-chain.

Please wait while we verify the transaction, receiving wallet, network, and amount."""


def get_payment_not_received_message(reason=None):
    detail = (
        f"\n\n{reason}"
        if reason
        else ""
    )
    return f"""❌ <b>Payment Not Received</b>

We could not verify the required payment on-chain.{detail}

Please check the transaction hash and try again."""


def get_payment_retry_buttons():
    return [
        ["🔄 Try Another Transaction Hash"],
        ["🔙 Back to Payment"],
        ["❌ Cancel"],
    ]


def get_payment_verified_message(
    order_id,
    service,
    platform,
    amount,
    token_name,
    transaction_hash,
):
    from html import escape

    return f"""✅ <b>Payment Verified - Thank You!</b>

Order ID: #{escape(str(order_id))}
Service: {escape(service)}
Platform: {escape(platform)}
Amount: {escape(amount)}
Token: {escape(token_name)}
Transaction:
<code>{escape(transaction_hash)}</code>

🕒 <b>Next Steps:</b>
1. Service activation begins within 3 hours
2. Results will appear on the platform shortly

⭐ Contact support with your Order ID for questions.

Would you like to place another order?"""
