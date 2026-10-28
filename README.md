# 🎮 PS GC Notifier

A Python bot that watches Indian game stores for **PlayStation gift cards** and pings you on **Telegram** and **Discord** the moment one comes back in stock. It runs for free in the cloud on GitHub Actions, so no server or always-on PC is needed.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-browser%20automation-2EAD33?logo=playwright&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-24%2F7-2088FF?logo=githubactions&logoColor=white)

---

## ✨ Features

- 🔔 **Instant alerts** on Telegram and Discord (Discord alerts use an `@everyone` mention)
- 🏪 **Multiple stores** tracked at once, with separate entries for each denomination (₹1,000 and ₹2,000)
- 🌐 **Real browser checks** with Playwright, so JavaScript-heavy shop pages are read correctly
- 🎯 **Per-store keyword rules** to avoid false alarms (for example, ignoring "notify me" text in a newsletter box)
- 🧠 **Remembers the last status** of each store and only alerts on a change from out of stock to in stock, so there's no spam
- ⏱️ **Checks every 2 minutes**
- ♻️ **Self-restarting 24/7 loop** on GitHub Actions, plus an optional external watchdog
- ⚠️ **Health warnings** if a page can't be read for many checks in a row

---

## 🧩 How it works

```
 GitHub Actions (check.yml, 5-hour loop)
        │
        ▼
 notifier.py ──► opens each store page in headless Chromium
        │            │
        │            ▼
        │       reads the visible text and looks for your
        │       in-stock / out-of-stock keywords
        │
        ├─ status changed to IN STOCK ─► Telegram + Discord alert
        └─ page unreadable 10x in a row ─► warning alert

 When the 5 hours end, the workflow starts itself again.
 cron-job.org also pokes GitHub as a backup watchdog.
```

---

## 🏪 Stores

| Store | Denominations | Status |
|---|---|---|
| Games The Shop | ₹1,000 / ₹2,000 | ✅ Active |
| GamersGift | ₹1,000 / ₹2,000 | ✅ Active |
| Rooter | ₹1,000 / ₹2,000 | ✅ Active |
| JioGames Store | n/a | ⛔ Disabled (blocks requests from GitHub's servers) |

---

## 📁 Project structure

```
ps-gc-notifier/
├── notifier.py            # the bot
├── config.json            # stores, URLs and keyword rules
├── requirements.txt       # Python dependencies
└── .github/workflows/
    ├── check.yml          # 24/7 stock-checking loop
    └── inspect.yml        # manual test ping to Telegram + Discord
```

---

## 🚀 Setup (cloud, free)

### 1. Fork or copy this repo
Make it **public** so GitHub Actions minutes are free. Your secrets are stored in GitHub Secrets, never in the code.

### 2. Create a Telegram bot
1. Message **@BotFather** on Telegram, send `/newbot`, and copy the token.
2. Open your new bot, tap **Start**, and send "hi".
3. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` and copy the number after `"chat":{"id":`. That's your chat ID.

### 3. Create a Discord webhook
In your Discord server: **Server Settings → Integrations → Webhooks → New Webhook**, pick a channel, and copy the webhook URL.

### 4. Create a GitHub token for the auto-restart
The workflow restarts itself with the GitHub CLI, which needs a token.
- Go to **Settings → Developer settings → Personal access tokens → Fine-grained tokens**.
- Limit it to **this repository only** and give it **Actions: Read and write**.
- (A classic token also works with the `repo` and `workflow` scopes.)

### 5. Add the secrets
In your repo go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret | What it is |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token from BotFather |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |
| `DISCORD_WEBHOOK_URL` | Your Discord webhook URL |
| `GH_PAT` | The GitHub token from step 4 |

### 6. Test your notifications
Open the **Actions** tab, choose **Inspect pages (manual)** (`inspect.yml`), and click **Run workflow**. In about 15 seconds you should get a test message on both Telegram and Discord.

### 7. Start the bot
Go to **Actions → Check PlayStation gift cards → Run workflow**. From then on it keeps itself running.

### 8. (Optional) Add an external watchdog
If a GitHub runner ever drops, a free [cron-job.org](https://cron-job.org) job can restart the loop. Create a job that sends:

- **URL:** `https://api.github.com/repos/<your-username>/ps-gc-notifier/actions/workflows/check.yml/dispatches`
- **Method:** `POST`
- **Headers:** `Authorization: Bearer <your token>` and `Accept: application/vnd.github+json`
- **Body:** `{"ref":"main"}`
- **Schedule:** every 10 to 30 minutes

The workflow's concurrency setting makes sure runs never overlap.

---

## ⚙️ Configuration

Everything lives in `config.json`.

```json
{
  "interval_minutes": 2,
  "sites": [
    {
      "name": "Example Store 1000",
      "url": "https://example.com/playstation-gift-card-1000",
      "browser": true,
      "out_of_stock_text": ["out of stock", "sold out"],
      "in_stock_text": ["add to cart"]
    }
  ]
}
```

| Option | Meaning |
|---|---|
| `interval_minutes` | Delay between full check rounds |
| `name` | Label used in alerts |
| `url` | Exact product page to watch |
| `enabled` | Set `false` to switch a store off |
| `browser` | `true` loads the page in headless Chromium (needed for JavaScript shops) |
| `out_of_stock_text` | Phrases that mean "not available". Checked first |
| `in_stock_text` | Phrases that mean "available" |
| `loading_text` | Placeholder words (for example `NaN`) meaning the page hasn't finished loading |
| `selector` | Optional CSS selector to read only part of the page |
| `wait_ms` | Extra wait after load so JavaScript can finish |

Tip: if a store gives wrong results, run `python notifier.py --inspect` to see exactly what text the bot reads, then adjust the keywords.

---

## 💻 Running locally (optional)

```bash
pip install -r requirements.txt
playwright install chromium
```

Set your secrets as environment variables. On Windows PowerShell:

```powershell
$env:TELEGRAM_BOT_TOKEN = "your-token"
$env:TELEGRAM_CHAT_ID = "your-chat-id"
$env:DISCORD_WEBHOOK_URL = "your-webhook-url"
```

Then:

```bash
python notifier.py --test      # send a test message
python notifier.py --inspect   # see what the bot reads on each page
python notifier.py --once      # check every store once
python notifier.py             # loop forever
```

---

## 🛠️ Troubleshooting

- **False "in stock" alerts:** run `--inspect`, find the real sold-out wording, and put it in that store's `out_of_stock_text`.
- **"No clear stock reading" warning:** the page changed or is blocking the bot. Check the URL and keywords.
- **A store works on your PC but not in the cloud:** some sites block GitHub's servers. That's why JioGames Store is disabled.
- **No Telegram or Discord message:** check the secret names and values, and make sure you sent your bot a message first.
- **Loop stopped:** run **Check PlayStation gift cards** manually, and set up the cron-job.org watchdog.

---

## 📌 Notes

- This is a personal project and isn't affiliated with Sony, PlayStation, or any of the stores listed.
- Keep your check interval reasonable and respect each store's terms of use.
- Never commit tokens or webhook URLs. Use GitHub Secrets.
