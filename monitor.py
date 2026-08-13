import os
import time
import requests
from playwright.sync_api import sync_playwright

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

URL = "https://tickets.pukkelpop.be/nl/meetup/demand/?type=combi&camping=a&price=all"

def send_alert():
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": (
                "🚨 PUKKELPOP ALERT! 🚨\n\n"
                "Er lijkt een Camping Chill / Camping A-ticket beschikbaar te zijn!\n\n"
                + URL
            ),
        },
        timeout=10,
    )

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    last_available = False

    while True:
        try:
            page.goto(URL, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)

            text = page.locator("body").inner_text().lower()

            available = (
                "geen tickets beschikbaar" not in text
                and (
                    "camping chill" in text
                    or "camping a" in text
                )
            )

            if available and not last_available:
                send_alert()

            last_available = available

            print("Beschikbaar:", available)

        except Exception as e:
            print("Fout:", e)

        time.sleep(5)
