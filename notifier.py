#!/usr/bin/env python3
"""
PlayStation gift card stock notifier -> Telegram & Discord.

Usage:
    python notifier.py --test      # send a test Telegram & Discord message
    python notifier.py --inspect   # show what the bot sees on each page (run this first)
    python notifier.py --once      # check every site once (cron / GitHub Actions)
    python notifier.py             # loop forever, every `interval_minutes`
"""
import argparse
import json
import logging
import os
import pathlib
import random
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

BASE = pathlib.Path(__file__).parent
CONFIG_PATH = BASE / "config.json"
STATE_PATH = BASE / "state.json"
INSPECT_DIR = BASE / "inspect"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

DEFAULT_OUT = [
    "out of stock", "sold out", "currently unavailable",
    "temporarily unavailable", "notify me", "coming soon",
]
DEFAULT_IN = ["add to cart", "buy now", "add to bag"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("psgc")


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def send_telegram(cfg, text):
    # Send to Telegram
    if cfg.get("telegram_bot_token") and cfg.get("telegram_chat_id"):
        try:
            url = f"https://api.telegram.org/bot{cfg['telegram_bot_token']}/sendMessage"
            r = requests.post(url, data={"chat_id": cfg["telegram_chat_id"], "text": text}, timeout=20)
            r.raise_for_status()
        except Exception as e:
            log.warning("Telegram send error: %s", e)

    # Send to Discord
    if cfg.get("discord_webhook_url"):
        try:
            r = requests.post(
                cfg["discord_webhook_url"],
                json={"content": f"@everyone {text}"},
                timeout=20,
            )
            r.raise_for_status()
        except Exception as e:
            log.warning("Discord send error: %s", e)


def fetch_html(site):
    if site.get("browser"):
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(user_agent=UA)
            page.goto(site["url"], wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(int(site.get("wait_ms", 4000)))
            html = page.content()
            browser.close()
        return html

    r = requests.get(
        site["url"],
        headers={"User-Agent": UA, "Accept-Language": "en-IN,en;q=0.9"},
        timeout=25,
    )
    r.raise_for_status()
    return r.text


def page_text(site):
    soup = BeautifulSoup(fetch_html(site), "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    if site.get("selector"):
        text = " ".join(n.get_text(" ") for n in soup.select(site["selector"]))
    else:
        text = soup.get_text(" ")
    return " ".join(text.split())


def classify(site, text):
    """Return 'in', 'out' or 'unknown'."""
    t = text.lower()
    for p in site.get("loading_text", []):
        if re.search(r"\b" + re.escape(p.lower()) + r"\b", t):
            return "unknown"
    if any(p.lower() in t for p in site.get("out_of_stock_text", DEFAULT_OUT)):
        return "out"
    if any(p.lower() in t for p in site.get("in_stock_text", DEFAULT_IN)):
        return "in"
    return "unknown"


def active_sites(cfg):
    for site in cfg["sites"]:
        if site.get("enabled", True) and not site["url"].startswith("PASTE"):
            yield site


def inspect(cfg):
    INSPECT_DIR.mkdir(exist_ok=True)
    for site in active_sites(cfg):
        name = site["name"]
        try:
            text = page_text(site)
        except Exception as e:
            print(f"\n=== {name}: ERROR {e}")
            continue
        slug = re.sub(r"[^a-z0-9]+", "_", name.lower())
        (INSPECT_DIR / f"{slug}.txt").write_text(text, encoding="utf-8")
        print(f"\n=== {name}: bot would say '{classify(site, text)}' ({len(text)} chars of text)")
        for p in DEFAULT_OUT + DEFAULT_IN:
            i = text.lower().find(p)
            if i != -1:
                print(f"   found '{p}': ...{text[max(0, i - 60): i + 80]}...")
    print(f"\nFull page text saved in {INSPECT_DIR}")


def run_cycle(cfg, state):
    for site in active_sites(cfg):
        name = site["name"]
        s = state.setdefault(name, {"status": "unknown", "bad": 0})
        try:
            status = classify(site, page_text(site))
        except Exception as e:
            log.warning("%s: error: %s", name, e)
            status = "error"
        log.info("%s: %s", name, status)

        if status == "in" and s["status"] != "in":
            send_telegram(cfg, f"🎮 PlayStation gift card looks IN STOCK on {name}!\n{site['url']}")

        if status in ("error", "unknown"):
            s["bad"] += 1
            if s["bad"] == 10:
                send_telegram(
                    cfg,
                    f"⚠️ {name}: no clear stock reading for 10 checks in a row. "
                    f"The page may have changed or is blocking the bot.\n{site['url']}",
                )
        else:
            s["bad"] = 0
            s["status"] = status

        STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
        time.sleep(random.uniform(2, 5))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--inspect", action="store_true")
    args = ap.parse_args()

    cfg = load_json(CONFIG_PATH, None)
    if not cfg:
        sys.exit("config.json missing or invalid.")

    cfg["telegram_bot_token"] = os.environ.get("TELEGRAM_BOT_TOKEN") or cfg.get("telegram_bot_token", "")
    cfg["telegram_chat_id"] = os.environ.get("TELEGRAM_CHAT_ID") or cfg.get("telegram_chat_id", "")
    cfg["discord_webhook_url"] = os.environ.get("DISCORD_WEBHOOK_URL") or cfg.get("discord_webhook_url", "")

    if args.test:
        send_telegram(cfg, "✅ PlayStation GC notifier is connected to Telegram & Discord!")
        print("Test message sent.")
        return
    if args.inspect:
        inspect(cfg)
        return

    state = load_json(STATE_PATH, {})
    if args.once:
        run_cycle(cfg, state)
        return

    interval = max(2, int(cfg.get("interval_minutes", 5)))
    while True:
        run_cycle(cfg, state)
        time.sleep(interval * 60 + random.uniform(0, 30))


if __name__ == "__main__":
    main()
