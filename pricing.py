# Pricing data for all services
# DexScreener Update - Same price for all blockchains (in USD)
DEXSCREENER_UPDATE_PRICING = { "all_chains": { "CTO Update": { "name": "CTO Update", "description": "Community Takeover Info Update", "price_usd": 199, "price": "$199" }, "Token Info Update": { "name": "Token Info Update", "description": "Full DexScreener Info Update", "price_usd": 299, "price": "$299" } } }
# DexScreener Trending - Different price per blockchain
DEXSCREENER_TRENDING_PRICING = { "Ethereum": { "Basic": {"price": "0.0949 ETH", "description": "Regular trending placement"}, "Advanced": {"price": "0.1583 ETH", "description": "Higher trending positions"}, "Premium": {"price": "0.2532 ETH", "description": "Top trending placements"} }, "BNB Chain": { "Basic": {"price": "0.3840 BNB", "description": "Regular trending placement"}, "Advanced": {"price": "0.6400 BNB", "description": "Higher trending positions"}, "Premium": {"price": "1.0240 BNB", "description": "Top trending placements"} }, "Polygon": { "Basic": {"price": "1.2000 MATIC", "description": "Regular trending placement"}, "Advanced": {"price": "2.0000 MATIC", "description": "Higher trending positions"}, "Premium": {"price": "3.2000 MATIC", "description": "Top trending placements"} }, "Arbitrum": { "Basic": {"price": "1.8000 ETH", "description": "Regular trending placement"}, "Advanced": {"price": "3.0000 ETH", "description": "Higher trending positions"}, "Premium": {"price": "4.8000 ETH", "description": "Top trending placements"} }, "Avalanche": { "Basic": {"price": "1.5000 AVAX", "description": "Regular trending placement"}, "Advanced": {"price": "2.5000 AVAX", "description": "Higher trending positions"}, "Premium": {"price": "4.0000 AVAX", "description": "Top trending placements"} }, "Fantom": { "Basic": {"price": "1.0500 FTM", "description": "Regular trending placement"}, "Advanced": {"price": "1.7500 FTM", "description": "Higher trending positions"}, "Premium": {"price": "2.8000 FTM", "description": "Top trending placements"} }, "Solana": { "Basic": {"price": "1.5000 SOL", "description": "Regular trending placement"}, "Advanced": {"price": "2.5000 SOL", "description": "Higher trending positions"}, "Premium": {"price": "4.0000 SOL", "description": "Top trending placements"} }, "Base": { "Basic": {"price": "1.3500 ETH", "description": "Regular trending placement"}, "Advanced": {"price": "2.2500 ETH", "description": "Higher trending positions"}, "Premium": {"price": "3.6000 ETH", "description": "Top trending placements"} }, "Cronos": { "Basic": {"price": "1.0500 CRO", "description": "Regular trending placement"}, "Advanced": {"price": "1.7500 CRO", "description": "Higher trending positions"}, "Premium": {"price": "2.8000 CRO", "description": "Top trending placements"} }, "Kava": { "Basic": {"price": "0.9000 KAVA", "description": "Regular trending placement"}, "Advanced": {"price": "1.5000 KAVA", "description": "Higher trending positions"}, "Premium": {"price": "2.4000 KAVA", "description": "Top trending placements"} }, "TRON": { "Basic": {"price": "0.8250 TRX", "description": "Regular trending placement"}, "Advanced": {"price": "1.3750 TRX", "description": "Higher trending positions"}, "Premium": {"price": "2.2000 TRX", "description": "Top trending placements"} }, "TON": { "Basic": {"price": "48.0000 TON", "description": "Regular trending placement"}, "Advanced": {"price": "80.0000 TON", "description": "Higher trending positions"}, "Premium": {"price": "128.0000 TON", "description": "Top trending placements"} }, "SUI": { "Basic": {"price": "1.2750 SUI", "description": "Regular trending placement"}, "Advanced": {"price": "2.1250 SUI", "description": "Higher trending positions"}, "Premium": {"price": "3.4000 SUI", "description": "Top trending placements"} } }
# DexScreener Volume - Different price per blockchain (7 tiers)
DEXSCREENER_VOLUME_PRICING = {
    blockchain: {
        tier: {
            "price": f"{amount} {currency}",
            "description": f"Generate {label} trading volume",
        }
        for tier, amount, label in [
            ("50K", "50K", "50K"),
            ("100K", "100K", "100K"),
            ("250K", "250K", "250K"),
            ("500K", "500K", "500K"),
            ("750K", "750K", "750K"),
            ("1M", "1M", "1M"),
            ("5M", "5M", "5M"),
        ]
    }
    for blockchain, currency in {
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
    }.items()
}

# Confirmed Volume Bot rates supplied in the latest pricing sheet.
_CONFIRMED_VOLUME_RATES = {
    "Cronos": {
        "750K": "15.7500 CRO",
        "1M": "21.0000 CRO",
        "5M": "105.0000 CRO",
    },
    "Kava": {
        "50K": "0.9000 KAVA",
        "100K": "1.8000 KAVA",
        "250K": "4.5000 KAVA",
        "500K": "9.0000 KAVA",
        "750K": "13.5000 KAVA",
        "1M": "18.0000 KAVA",
        "5M": "90.0000 KAVA",
    },
    "TRON": {
        "50K": "0.8250 TRX",
        "100K": "1.6500 TRX",
        "250K": "4.1250 TRX",
        "500K": "8.2500 TRX",
        "750K": "12.3750 TRX",
        "1M": "16.5000 TRX",
        "5M": "82.5000 TRX",
    },
    "TON": {
        "50K": "48.0000 TON",
        "100K": "96.0000 TON",
        "250K": "240.0000 TON",
        "500K": "480.0000 TON",
        "750K": "720.0000 TON",
        "1M": "960.0000 TON",
        "5M": "4800.0000 TON",
    },
    "SUI": {
        "50K": "1.2750 SUI",
        "100K": "2.5500 SUI",
        "250K": "6.3750 SUI",
        "500K": "12.7500 SUI",
        "750K": "19.1250 SUI",
        "1M": "25.5000 SUI",
        "5M": "127.5000 SUI",
    },
}

for _blockchain, _rates in _CONFIRMED_VOLUME_RATES.items():
    for _tier, _price in _rates.items():
        DEXSCREENER_VOLUME_PRICING[_blockchain][_tier]["price"] = _price

for _tier in ["50K", "100K", "250K", "500K"]:
    DEXSCREENER_VOLUME_PRICING["Cronos"][_tier]["price"] = "Price to be confirmed"

# DexScreener Boost pricing from the supplied Boost write-up.
_VOLUME_MULTIPLIERS = {
    "50K": "1",
    "100K": "2",
    "250K": "5",
    "500K": "10",
    "750K": "15",
    "1M": "20",
    "5M": "100",
}

from decimal import Decimal

for _blockchain, _trending in DEXSCREENER_TRENDING_PRICING.items():
    _base_price, _currency = _trending["Basic"]["price"].split()
    _base_amount = Decimal(_base_price)
    for _tier, _multiplier in _VOLUME_MULTIPLIERS.items():
        DEXSCREENER_VOLUME_PRICING[_blockchain][_tier]["price"] = (
            f"{_base_amount * Decimal(_multiplier):.4f} {_currency}"
        )

_BOOST_RATES = {
    "Ethereum": {
        "2x Boost": "0.0633 ETH",
        "4x Boost": "0.1266 ETH",
        "6x Boost": "0.1899 ETH",
    },
    "BNB Chain": {
        "2x Boost": "0.2560 BNB",
        "4x Boost": "0.5120 BNB",
        "6x Boost": "0.7680 BNB",
    },
    "Polygon": {
        "2x Boost": "0.8000 MATIC",
        "4x Boost": "1.6000 MATIC",
        "6x Boost": "2.4000 MATIC",
    },
    "Arbitrum": {
        "2x Boost": "1.2000 ETH",
        "4x Boost": "2.4000 ETH",
        "6x Boost": "3.6000 ETH",
    },
    "Avalanche": {
        "2x Boost": "1.0000 AVAX",
        "4x Boost": "2.0000 AVAX",
        "6x Boost": "3.0000 AVAX",
    },
    "Fantom": {
        "2x Boost": "0.7000 FTM",
        "4x Boost": "1.4000 FTM",
        "6x Boost": "2.1000 FTM",
    },
    "Solana": {
        "2x Boost": "1.0000 SOL",
        "4x Boost": "2.0000 SOL",
        "6x Boost": "3.0000 SOL",
    },
    "Base": {
        "2x Boost": "0.9000 ETH",
        "4x Boost": "1.8000 ETH",
        "6x Boost": "2.7000 ETH",
    },
    "Cronos": {
        "2x Boost": "0.7000 CRO",
        "4x Boost": "1.4000 CRO",
        "6x Boost": "2.1000 CRO",
    },
    "Kava": {
        "2x Boost": "0.6000 KAVA",
        "4x Boost": "1.2000 KAVA",
        "6x Boost": "1.8000 KAVA",
    },
    "TRON": {
        "2x Boost": "0.5500 TRX",
        "4x Boost": "1.1000 TRX",
        "6x Boost": "1.6500 TRX",
    },
    "TON": {
        "2x Boost": "32.0000 TON",
        "4x Boost": "64.0000 TON",
        "6x Boost": "96.0000 TON",
    },
    "SUI": {
        "2x Boost": "0.8500 SUI",
        "4x Boost": "1.7000 SUI",
        "6x Boost": "2.5500 SUI",
    },
}
DEXSCREENER_BOOST_PRICING = {
    blockchain: {
        tier: {
            "price": price,
            "description": {
                "2x Boost": "Double visibility",
                "4x Boost": "4x enhanced visibility",
                "6x Boost": "6x premium visibility",
            }[tier],
        }
        for tier, price in pricing.items()
    }
    for blockchain, pricing in _BOOST_RATES.items()
}

PUMPFUN_BOOST_PRICING = {
    "Basic Pump": {
        "price": "0.5000 SOL",
        "description": "Light volume and holder increase",
    },
    "Medium Pump": {
        "price": "1.0000 SOL",
        "description": "Moderate volume and holder boost",
    },
    "Mega Pump": {
        "price": "2.0000 SOL",
        "description": "Heavy volume and maximum holder boost",
    },
}

PUMPFUN_TRENDING_PRICING = {
    "Trending Basic": {
        "price": "1.0000 SOL",
        "description": "Basic trending placement",
    },
    "Trending Advanced": {
        "price": "1.8000 SOL",
        "description": "Higher trending position",
    },
    "Trending Premium": {
        "price": "3.0000 SOL",
        "description": "Top trending spots",
    },
}

PUMPFUN_VOLUME_PRICING = {
    "50K Volume": {
        "price": "1.5000 SOL",
        "description": "Generate 50k trading volume",
    },
    "100K Volume": {
        "price": "3.0000 SOL",
        "description": "Generate 100k trading volume",
    },
    "250K Volume": {
        "price": "7.5000 SOL",
        "description": "Generate 250k trading volume",
    },
    "500K Volume": {
        "price": "15.0000 SOL",
        "description": "Generate 500k trading volume",
    },
    "750K Volume": {
        "price": "22.5000 SOL",
        "description": "Generate 750k trading volume",
    },
    "1M Volume": {
        "price": "30.0000 SOL",
        "description": "Generate 1M trading volume",
    },
    "5M Volume": {
        "price": "150.0000 SOL",
        "description": "Generate 5M trading volume",
    },
}

PUMPFUN_GRADUATION_PRICING = {
    "Graduation Assist": {
        "price": "2.5000 SOL",
        "description": "Moderate push towards graduation",
    },
    "Graduation Boost": {
        "price": "4.0000 SOL",
        "description": "Strong push with volume burst",
    },
    "Graduation Express": {
        "price": "6.0000 SOL",
        "description": "Maximum graduation assistance",
    },
}

FOURMEME_BOOST_PRICING = {
    "Basic Pump": {
        "price": "0.3000 BNB",
        "description": "Light volume and holder increase",
    },
    "Medium Pump": {
        "price": "0.6000 BNB",
        "description": "Moderate volume and holder boost",
    },
    "Mega Pump": {
        "price": "1.0000 BNB",
        "description": "Heavy volume and maximum holder boost",
    },
}

FOURMEME_TRENDING_PRICING = {
    "Trending Basic": {
        "price": "0.0640 BNB",
        "description": "Basic Four.Meme trending placement",
    },
    "Trending Advanced": {
        "price": "0.1280 BNB",
        "description": "Higher trending position",
    },
    "Trending Premium": {
        "price": "0.2560 BNB",
        "description": "Top trending spots on Four.Meme",
    },
}

FOURMEME_VOLUME_PRICING = {
    "50K Volume": {
        "price": "0.3840 BNB",
        "description": "Generate 50K trading volume",
    },
    "100K Volume": {
        "price": "0.7680 BNB",
        "description": "Generate 100K trading volume",
    },
    "250K Volume": {
        "price": "1.9200 BNB",
        "description": "Generate 250K trading volume",
    },
    "500K Volume": {
        "price": "3.8400 BNB",
        "description": "Generate 500K trading volume",
    },
    "750K Volume": {
        "price": "5.7600 BNB",
        "description": "Generate 750K trading volume",
    },
    "1M Volume": {
        "price": "7.6800 BNB",
        "description": "Generate 1M trading volume",
    },
    "5M Volume": {
        "price": "38.4000 BNB",
        "description": "Generate 5M trading volume",
    },
}

FLAPSH_BOOST_PRICING = FOURMEME_BOOST_PRICING
FLAPSH_TRENDING_PRICING = FOURMEME_TRENDING_PRICING
FLAPSH_VOLUME_PRICING = FOURMEME_VOLUME_PRICING

# Robinhood uses the same ETH pricing and tier descriptions as Ethereum.
from copy import deepcopy

for _pricing_table in (
    DEXSCREENER_TRENDING_PRICING,
    DEXSCREENER_VOLUME_PRICING,
    DEXSCREENER_BOOST_PRICING,
):
    _pricing_table["Robinhood"] = deepcopy(_pricing_table["Ethereum"])