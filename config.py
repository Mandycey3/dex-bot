# Configuration file for Dex Boosting Bot
import os


def _load_local_env(path):
    """Load simple KEY=VALUE entries without overriding Replit Secrets."""
    try:
        with open(path, encoding="utf-8") as env_file:
            lines = env_file.readlines()
    except FileNotFoundError:
        return

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key, value)


_load_local_env(os.path.join(os.path.dirname(__file__), ".env"))

# Store the real token in Replit Secrets as TELEGRAM_BOT_TOKEN.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

# All supported blockchains
BLOCKCHAINS = [ "Ethereum", "Robinhood", "BNB Chain", "Polygon", "Arbitrum", "Avalanche", "Fantom", "Solana", "Base", "Cronos", "Kava", "TRON", "TON", "SUI" ]

# Bot messages
WELCOME_MESSAGE = """👋 <b>Welcome to the Multi-Platform Token Booster Bot!</b>

Ready to send your token to the moon? 🚀
We provide industry-leading automated volume, holders, and Trending services across the top crypto platforms with unmatched reliability and speed.

⚠️ <b>IMPORTANT NOTICE:</b>
This bot is <b>NOT a product of DexScreener</b>. We are an independent service that connects directly to the DexScreener API to ensure your project's data remains accurate and top-performing at all times.

✨ <b>Why Choose Us?</b>
• <b>Trusted by Professionals:</b> We are a verified provider for top-tier crypto projects.
• <b>Direct API Integration:</b> We use official channels to ensure 100% safety and performance.
• <b>24/7 Premium Support:</b> Our team is always here to help you scale your project.

📈 <b>Our Supported Platforms:</b>
📉 <b>DexScreener</b> – Maximize visibility with trending status and high-speed volume bots.
🔥 <b>Pump.fun</b> – Supercharge your Solana launches with tailored volume &amp; holders.
🐸 <b>Four.Meme</b> – Dominate the BSC meme coin charts like a pro.
⚡ <b>Flap.sh</b> – Automate your BSC project volume and trending status.

💡 Whether you're stealth launching or scaling a massive <b>Community Takeover (CTO)</b>, we have the premium tools you need to build unbreakable hype and investor trust.

👇 <b>Select a platform below to get started!</b>"""

ABOUT_MESSAGE = """<b>About Multi-Platform Token Booster Bot</b>

This bot provides premium services to enhance your token's performance across multiple platforms.

Our services help you increase token visibility, get trending placements, and boost trading volume statistics."""

SUPPORT_MESSAGE = """<b>Customer Support</b>

If you need assistance, please contact our support team:

• Telegram: @Drakesmart
Our support team is available 24/7."""

# Main menu keyboard layout
MAIN_MENU_BUTTONS = [
    ["DexScreener", "Pump.fun"],
    ["Four.Meme", "Flap.sh"],
    ["About", "Support"],
]

# DexScreener services
DEXSCREENER_SERVICES = [ ["DexScreener Update", "DexScreener Trending"], ["DexScreener Volume", "DexScreener Boost"], ["🔙 Back to Main Menu"] ]

# Pump.fun is Solana-only, so this menu intentionally has no blockchain step.
PUMPFUN_SERVICES = [
    ["Pump.fun Boost", "Pump.fun Trending"],
    ["Pump.fun Volume", "Pump.fun Graduation"],
    ["🔙 Back to Main Menu"],
]

# Four.Meme is BNB Chain-only, so this menu intentionally has no blockchain step.
FOURMEME_SERVICES = [
    ["Four.Meme Boost", "Four.Meme Trending"],
    ["Four.Meme Volume", "🔙 Back to Main Menu"],
]

# Flap.sh is BNB Chain-only, so this menu intentionally has no blockchain step.
FLAPSH_SERVICES = [
    ["Flap.sh Boost", "Flap.sh Trending"],
    ["Flap.sh Volume", "🔙 Back to Main Menu"],
]