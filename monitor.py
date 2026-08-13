import os
import time
import threading
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
from playwright.sync_api import sync_playwright

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

URL = "https://tickets.pukkelpop.be/nl/meetup/demand/?type=combi&camping=a&price=all"


# Render moet een poort kunnen bereiken
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"PKP Camping Alert is running")

    def log_message(self, format, *args):
        pass


def start_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


threading.Thread(target=start_server, daemon=True).start()


def send_alert():
    try:
        response = requests.post(
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

        print("Telegram status:", response.status_code)

        if response.ok:
            print("🚨 Telegram melding verstuurd!")
        else:
            print("⚠️ Telegram fout:", response.text)

    except Exception as e:
        print("⚠️ Telegram fout:", e)


print("🌐 PKP Camping Alert gestart")

with sync_playwright() as p:
    print("🚀 Chromium starten...")

    browser = p.chromium.launch(
        headless=True,
        args=["--no-sandbox"]
    )

    page = browser.new_page()

    last_available = False

    while True:
        try:
            print("🔎 Pukkelpop controleren...")

            page.goto(
                URL,
                wait_until="domcontentloaded",
                timeout=30000
            )

            page.wait_for_timeout(3000)

            text = page.locator("body").inner_text().lower()

            available = (
                "geen tickets beschikbaar" not in text
                and (
                    "camping chill" in text
                    or "camping a" in text
                )
            )

            print("Beschikbaar:", available)

            if available and not last_available:
                send_alert()

            last_available = available

        except Exception as e:
            print("⚠️ Controlefout:", e)

        time.sleep(5)
