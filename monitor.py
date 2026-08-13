```python
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

CHECK_INTERVAL = 2
NOTIFICATION_INTERVAL = 2


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

        page.wait_for_timeout(500)

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

    try:
        send_telegram(
            "🟢 PKP Monitor is gestart!\n\n"
            "Ik controleer:\n"
            "🎟️ Zaterdag zonder camping\n"
            "🏕️ Combi + Camping Chill\n\n"
            "Controle elke 2 seconden."
        )

        print("📲 Telegram verbinding OK", flush=True)

    except Exception as e:
        print(f"❌ Telegram verbinding mislukt: {e}", flush=True)

    last_notification = {
        "Zaterdag zonder camping": 0,
        "Combi + Camping Chill": 0,
    }

    ticket_available = {
        "Zaterdag zonder camping": False,
        "Combi + Camping Chill": False,
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        while True:
            loop_start = time.time()

            for name, info in TICKETS.items():

                available = check_ticket(page, name, info)
                current_time = time.time()

                if available:
                    ticket_available[name] = True

                    if (
                        current_time - last_notification[name]
                        >= NOTIFICATION_INTERVAL
                    ):
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

                            last_notification[name] = current_time

                        except Exception as e:
                            print(
                                f"⚠️ Telegram-fout: {e}",
                                flush=True,
                            )

                else:
                    if ticket_available[name]:
                        print(
                            f"🔴 {name}: ticket niet meer beschikbaar",
                            flush=True,
                        )

                    ticket_available[name] = False
                    last_notification[name] = 0

            elapsed = time.time() - loop_start
            wait_time = max(0, CHECK_INTERVAL - elapsed)

            print(
                f"⏱️ Volgende controle over "
                f"{wait_time:.1f} seconden...",
                flush=True,
            )

            time.sleep(wait_time)


if __name__ == "__main__":
    main()
```
