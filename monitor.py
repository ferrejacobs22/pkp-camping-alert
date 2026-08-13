import os
import time
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

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

CHECK_INTERVAL = 10


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

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


def check_ticket(page, name, info):
    print(f"🔎 Controle: {name}", flush=True)

    try:
        page.goto(
            info["url"],
            wait_until="domcontentloaded",
            timeout=30000,
        )

        page.wait_for_timeout(2000)

        text = page.locator("body").inner_text().lower()

        if "geen tickets beschikbaar" in text:
            print(f"❌ {name}: geen tickets", flush=True)
            return False

        print(f"🚨 {name}: MOGELIJK BESCHIKBAAR!", flush=True)
        return True

    except Exception as e:
        print(f"⚠️ Fout bij {name}: {e}", flush=True)
        return False


def main():
    print("================================", flush=True)
    print("🟢 PKP MONITOR GESTART", flush=True)
    print("================================", flush=True)

    # Telegram testen bij het opstarten
    try:
        send_telegram(
            "🟢 PKP Monitor is gestart!\n\n"
            "Ik controleer:\n"
            "🎟️ Zaterdag zonder camping\n"
            "🏕️ Combi + Camping Chill\n\n"
            "Controle elke 10 seconden."
        )
        print("📲 Telegram verbinding OK", flush=True)

    except Exception as e:
        print(f"❌ Telegram verbinding mislukt: {e}", flush=True)

    already_notified = {
        "Zaterdag zonder camping": False,
        "Combi + Camping Chill": False,
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        while True:
            for name, info in TICKETS.items():
                available = check_ticket(page, name, info)

                if available and not already_notified[name]:
                    message = (
                        f"{info['emoji']} PKP TICKET BESCHIKBAAR!\n\n"
                        f"{name}\n\n"
                        f"{info['url']}"
                    )

                    try:
                        send_telegram(message)
                        print(
                            f"📲 Telegram verstuurd: {name}",
                            flush=True,
                        )
                        already_notified[name] = True

                    except Exception as e:
                        print(
                            f"⚠️ Telegram-fout: {e}",
                            flush=True,
                        )

                elif not available:
                    already_notified[name] = False

            print(
                f"⏱️ Volgende controle over {CHECK_INTERVAL} seconden...",
                flush=True,
            )

            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
