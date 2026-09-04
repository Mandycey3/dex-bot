# DEX Telegram Bot

This project provides a Telegram ordering flow for DexScreener services,
on-chain payment verification, rotating receiving wallets, and a small
password-protected wallet admin page.

## Included services

- DexScreener update, trending, volume, and boost order flows
- Four.Meme Boost, Trending, and Volume order flows on BNB Chain
- Flap.sh Boost, Trending, and Volume order flows on BNB Chain
- Multi-source token lookup through GeckoTerminal, CoinGecko, Jupiter,
  on-chain ERC-20 metadata, and a final DexScreener enrichment fallback
- EVM and Solana native-payment verification
- PostgreSQL-backed payment and wallet state
- Least-recently-used wallet assignment per blockchain
- Password-protected wallet rotation page on the configured web port
- Password-protected admin controls for banning and unbanning Telegram users
- Optional owner notifications for incoming bot activity

## Configuration

The bot intentionally does not ship with a populated `.env` file. Add these
values as Replit Secrets:

- `TELEGRAM_BOT_TOKEN` — token from BotFather
- `ADMIN_PASSWORD` — password for the wallet admin page
- `BOT_ACTIVITY_OWNER_CHAT_ID` — Telegram chat ID that receives activity alerts

`SESSION_SECRET` is already available as a project secret and is used to sign
the admin session cookie. Optional settings are documented in `.env.example`.

`DATABASE_URL` is supplied by the project's PostgreSQL database.

The admin page also includes User access controls. Enter a Telegram user ID to
ban or unban that user. Bans block bot usage without deleting payment history.

## Database setup

The shared Drizzle schema in `lib/db/src/schema/dexBot.ts` is the source of
truth for the bot tables. After the schema is pushed, import the current
public receiving-wallet addresses from `wallets.csv` with:

```bash
python dex-bot/seed_wallets.py
```

The seed is safe to rerun. It replaces the active wallet pool for each chain
represented in the CSV while leaving other chains untouched.

## Running

The configured `DEX Bot` workflow runs:

```bash
python dex-bot/bot.py
```

The Telegram token is required before the bot can start polling. The wallet
admin page uses the same process and listens on `PORT` (default `5000`).

## Important operational note

The order flow accepts payment and verifies native transfers, but service
fulfillment remains a queued state. Connect the actual fulfillment provider
before treating confirmed payments as completed service delivery.