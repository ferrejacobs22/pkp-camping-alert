import os
import time
import threading
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
from playwright.sync_api import sync_playwright
# =========================
# INSTELLINGEN
# =========================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
URL = "https://tickets.pukkelpop.be/nl/meetup/demand/?type=combi&camping=a&price=all"
# =========================
# RENDER HEALTH SERVER
# =========================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"PKP Camping Alert is running")
    def log_message(self, format, *args):
        pass
def start_server():
    port = int(os.environ.get("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()
threading.Thread(target=start_server, daemon=True).start()
# =========================
# TELEGRAM
# =========================
def send_alert():
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": (
                    "🚨 PUKKELPOP ALERT! 🚨\n\n"
                    "Er is mogelijk een ticket beschikbaar!\n\n"
                    "🎟️ Camping A / Combi\n\n"
                    f"{URL}"
                ),
            },
            timeout=10,
        )
        if response.ok:
            print("🚨 Telegram melding verstuurd!")
        else:
            print("⚠️ Telegram fout:", response.text)
    except Exception as e:
        print("⚠️ Telegram fout:", e)
# =========================
# TICKET CONTROLE
# =========================
def check_ticket(page):
    page.goto(
        URL,
        wait_until="domcontentloaded",
        timeout=30000
    )
    page.wait_for_timeout(3000)
    text = page.locator("body").inner_text().lower()
    # De belangrijkste controle:
    # Als deze tekst aanwezig is, zijn er GEEN tickets.
    no_tickets = "geen tickets beschikbaar" in text
    if no_tickets:
        return False
    # Extra controle om foutieve meldingen te vermijden.
    # We kijken of er daadwerkelijk een ticket-gerelateerde
    # koop/aanbodtekst op de pagina staat.
    ticket_words = [
        "bestellen",
        "koop",
        "kopen",
        "toevoegen",
        "beschikbaar",
        "ticket"
    ]
    found_ticket_text = any(word in text for word in ticket_words)
    return found_ticket_text
# =========================
# START
# =========================
print("🌐 PKP Camping Alert gestart")
with sync_playwright() as p:
    print("🚀 Chromium starten...")
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage"
        ]
    )
    page = browser.new_page()
    last_available = False
    while True:
        try:
            print("🔎 Pukkelpop controleren...")
            available = check_ticket(page)
            print("Beschikbaar:", available)
            # Alleen melden wanneer de status verandert:
            # False -> True
            if available and not last_available:
                send_alert()
            # Status onthouden
            last_available = available
        except Exception as e:
            print("⚠️ Controlefout:", e)
            # Browserpagina opnieuw proberen bij een fout
            try:
                page.close()
            except:
                pass
            page = browser.new_page()
        # 5 seconden wachten
        time.sleep(5)
