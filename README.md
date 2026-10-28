# 🎮 PS Gift Card Notifier

A small Python bot that watches PlayStation gift card pages on Indian stores and sends you a **Telegram message** the moment one comes back in stock.

It runs **free in the cloud on GitHub Actions**, so there's no server to rent and nothing to keep running on your PC.

## How it works

1. Every ~5 minutes, GitHub Actions starts the bot.
2. The bot opens each store page in a headless browser (Playwright), so JavaScript-loaded stock info shows up.
3. It reads the visible page text and decides if the card is **in stock**, **out of stock** or **unclear**.
4. If a card goes from *not in stock* to *in stock*, you get a Telegram alert with the link.
5. It saves the last status in `state.json`, so you only get alerted when something changes, not on every check.

If a page gives no clear reading 10 checks in a row, the bot warns you that the page may have changed or is blocking it.

## Stores watched

- Games The Shop
- GamersGift
- JioGames Store
- Rooter

You can add or remove stores by editing `config.json`.

## Project files

| File | What it does |
| --- | --- |
| `notifier.py` | The bot: loads pages, checks stock, sends Telegram alerts |
| `config.json` | The list of store pages to watch, plus per-site tweaks |
| `requirements.txt` | Python libraries needed |
| `.github/workflows/check.yml` | Runs the bot every ~5 minutes |
| `.github/workflows/inspect.yml` | Manual run that shows what the bot sees on each page |

## Set it up yourself

You don't need to code for this, only edit one file.

1. **Make a Telegram bot.** Message [@BotFather](https://t.me/BotFather), send `/newbot`, and copy the token. Then message your new bot once (e.g. "hi") and open `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your chat ID.
2. **Copy this project.** Fork this repo, or create your own and upload these files.
3. **Add secrets.** In your repo go to *Settings → Secrets and variables → Actions* and add:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. **Enable Actions.** Open the *Actions* tab and enable workflows if GitHub asks.
5. **Check what the bot sees.** Run **Inspect pages (manual)** from the Actions tab, then open the run and expand *Show what the bot sees*.
6. **Tune the config** (see below) if a store's wording is different.
7. **Start it.** Run **Check PlayStation gift cards** once. After that it runs on its own.

> Never put your bot token in a file or commit it. It belongs in GitHub Secrets only.

## Customising `config.json`

Each store is an entry in the `sites` list:

```json
{
  "name": "JioGames Store",
  "url": "https://store.jiogames.com/products/?brand=playstation",
  "browser": true,
  "out_of_stock_text": ["no products found"]
}
```

| Option | Meaning |
| --- | --- |
| `name` | Name shown in the alert |
| `url` | The exact product page to watch |
| `browser` | `true` to load the page in a real browser (needed for most stores) |
| `out_of_stock_text` | Phrases that mean the card is **not** available |
| `in_stock_text` | Phrases that mean the card **is** available |
| `loading_text` | Placeholder text (e.g. `NaN`) meaning the page hasn't finished loading |
| `selector` | Only read part of the page (CSS selector) |
| `wait_ms` | Extra wait for slow pages (default 4000) |
| `enabled` | Set to `false` to pause a store |

If nothing is set, the bot falls back to common phrases like "out of stock", "sold out", "add to cart" and "buy now".

## Running it on your own computer (optional)

```bash
pip install -r requirements.txt
playwright install chromium

export TELEGRAM_BOT_TOKEN="your-token"
export TELEGRAM_CHAT_ID="your-chat-id"

python notifier.py --inspect   # see what the bot sees on each page
python notifier.py --once      # check every store once
python notifier.py             # keep checking every few minutes
```

On Windows Command Prompt, use `set TELEGRAM_BOT_TOKEN=your-token` instead of `export`.

## Good to know

- Stock detection is text-based, so a store redesign can break a check. That's what the "no clear reading" warning is for.
- GitHub Actions timing isn't exact. Runs can start a few minutes late.
- Keep the check interval reasonable so you don't hammer the stores.
- This is a personal project and isn't affiliated with PlayStation, Sony or any of the stores.

## Built with

Python · Playwright · BeautifulSoup · Requests · GitHub Actions · Telegram Bot API
