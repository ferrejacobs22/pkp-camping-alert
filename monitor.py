import os
import time
import threading
import requests

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from playwright.sync_api import sync_playwright


# =========================
# INSTELLINGEN
# =========================

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

CHECK_INTERVAL = 2

TICKETS = {
    "Zaterdag zonder camping": {
        "url": "https://tickets.pukkelpop.be/nl/meetup/demand/?type=day2&camping=n&price=all#tickets",
        "emoji": "🎟️",
    },
    "Combi + Camping Chill": {
        "url": "https://tickets.pukkelpop.be/nl/meetup/demand/?type=combi&camping=a&price=all#tickets",
        "emoji": "🏕️",
    },
}


# =========================
# KLEINE WEBSERVER VOOR RENDER
# =========================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"PKP Monitor is running!")

    def log_message(self, format, *args):
        return


def start_web_server():
    port = int(os.environ.get("PORT", 10000))

    server = ThreadingHTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    print(f"🌐 Webserver gestart op poort {port}", flush=True)

    server.serve_forever()


# =========================
# TELEGRAM
# =========================

def send_telegram(message):
    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "disable_web_page_preview": False,
        },
        timeout=10,
    )

    response.raise_for_status()


# =========================
# TICKET CONTROLE
# =========================

def check_ticket(page, name, info):

    print(f"🔎 Controle: {name}", flush=True)

    try:

        page.goto(
            info["url"],
            wait_until="domcontentloaded",
            timeout=30000,
        )

        page.wait_for_timeout(1000)

        text = page.locator("body").inner_text().lower()

        if "geen tickets beschikbaar" in text:
            print(
                f"❌ {name}: geen tickets",
                flush=True
            )
            return False

        print(
            f"🚨 {name}: MOGELIJK BESCHIKBAAR!",
            flush=True
        )

        return True

    except Exception as e:

        print(
            f"⚠️ Fout bij {name}: {e}",
            flush=True
        )

        return False


# =========================
# HOOFDPROGRAMMA
# =========================

def main():

    print("================================", flush=True)
    print("🟢 PKP MONITOR GESTART", flush=True)
    print("================================", flush=True)

    # Telegram testen
    try:

        send_telegram(
            "🟢 PKP Monitor is gestart!\n\n"
            "Ik controleer:\n"
            "🎟️ Zaterdag zonder camping\n"
            "🏕️ Combi + Camping Chill\n\n"
            "Controle elke 2 seconden."
        )

        print(
            "📲 Telegram verbinding OK",
            flush=True
        )

    except Exception as e:

        print(
            f"❌ Telegram verbinding mislukt: {e}",
            flush=True
        )


    # Houd bij of er momenteel tickets zijn
    ticket_status = {
        "Zaterdag zonder camping": False,
        "Combi + Camping Chill": False,
    }


    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        page = browser.new_page()


        while True:

            for name, info in TICKETS.items():

                available = check_ticket(
                    page,
                    name,
                    info
                )


                # =========================
                # TICKET GEVONDEN
                # =========================

                if available:

                    # Alleen wanneer het ticket
                    # net beschikbaar is geworden
                    if not ticket_status[name]:

                        message = (
                            f"🚨 {info['emoji']} "
                            f"PKP TICKET BESCHIKBAAR!\n\n"
                            f"🎟️ {name}\n\n"
                            f"👉 {info['url']}"
                        )

                        try:

                            send_telegram(message)

                            print(
                                f"📲 Telegram verstuurd: {name}",
                                flush=True
                            )

                        except Exception as e:

                            print(
                                f"⚠️ Telegram-fout: {e}",
                                flush=True
                            )


                    # Ticket staat nog steeds online
                    # -> opnieuw melding sturen
                    else:

                        message = (
                            f"🔥 {info['emoji']} "
                            f"PKP TICKET NOG STEEDS BESCHIKBAAR!\n\n"
                            f"🎟️ {name}\n\n"
                            f"👉 {info['url']}"
                        )

                        try:

                            send_telegram(message)

                            print(
                                f"📲 Herhaalde melding: {name}",
                                flush=True
                            )

                        except Exception as e:

                            print(
                                f"⚠️ Telegram-fout: {e}",
                                flush=True
                            )


                    ticket_status[name] = True


                # =========================
                # TICKET WEG
                # =========================

                else:

                    if ticket_status[name]:

                        print(
                            f"ℹ️ {name}: ticket lijkt weer weg",
                            flush=True
                        )

                    ticket_status[name] = False


            print(
                f"⏱️ Volgende controle over "
                f"{CHECK_INTERVAL} seconden...",
                flush=True
            )

            time.sleep(CHECK_INTERVAL)


# =========================
# START
# =========================

if __name__ == "__main__":

    # Render-webserver in aparte thread
    web_thread = threading.Thread(
        target=start_web_server,
        daemon=True
    )

    web_thread.start()

    # Ticketmonitor starten
    main()
