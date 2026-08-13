import os
import time
import threading
import requests
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from playwright.sync_api import sync_playwright
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
URL = "https://tickets.pukkelpop.be/nl/meetup/demand/?type=combi&camping=a&price=all"
CHECK_INTERVAL = 5
HEARTBEAT_INTERVAL = 600  # 10 minuten
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
def send_telegram(message):
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": message,
            },
            timeout=10,
        )
        if response.ok:
            print("✅ Telegram melding verstuurd", flush=True)
        else:
            print(
                f"⚠️ Telegram fout: {response.status_code} {response.text}",
                flush=True,
            )
    except Exception as e:
        print(f"⚠️ Telegram verbindingsfout: {e}", flush=True)
def send_heartbeat():
    now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    send_telegram(
        "🟢 PKP MONITOR ACTIEF\n\n"
        f"De monitor draait nog steeds.\n"
        f"Heartbeat: {now}\n\n"
        "Controleert elke 5 seconden."
    )
threading.Thread(target=start_server, daemon=True).start()
print("🌐 PKP Camping Alert gestart", flush=True)
last_available = False
last_heartbeat = time.monotonic()
with sync_playwright() as p:
    print("🚀 Chromium starten...", flush=True)
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ],
    )
    page = browser.new_page()
    while True:
        try:
            # Heartbeat om de 10 minuten
            if time.monotonic() - last_heartbeat >= HEARTBEAT_INTERVAL:
                send_heartbeat()
                last_heartbeat = time.monotonic()
            print("🔎 Pukkelpop controleren...", flush=True)
            page.goto(
                URL,
                wait_until="domcontentloaded",
                timeout=30000,
            )
            # Wacht alleen tot de pagina inhoud heeft.
            # Geen vaste 3 seconden wachttijd meer.
            try:
                page.wait_for_selector("body", timeout=5000)
            except Exception:
                pass
            text = page.locator("body").inner_text().lower()
            # De belangrijkste controle:
            # Als "geen tickets beschikbaar" op de pagina staat,
            # is er momenteel geen ticket.
            no_tickets = "geen tickets beschikbaar" in text
            available = not no_tickets
            print(f"Beschikbaar: {available}", flush=True)
            # Alleen melden wanneer de status van GEEN
            # naar WEL beschikbaar verandert.
            if available and not last_available:
                send_telegram(
                    "🚨 PUKKELPOP TICKET ALERT! 🚨\n\n"
                    "Er lijkt een ticket beschikbaar te zijn!\n\n"
                    f"{URL}"
                )
            last_available = available
        except Exception as e:
            print(f"⚠️ Controlefout: {e}", flush=True)
        time.sleep(CHECK_INTERVAL)
