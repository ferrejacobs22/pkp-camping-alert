import os
import time
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

URL = "https://tickets.pukkelpop.be/nl/meetup/demand/?type=combi&camping=a&price=all"

def send_message(message):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": message},
        timeout=10
    )

last_available = False

while True:
    try:
        response = requests.get(URL, timeout=15)
        text = response.text.lower()

        available = (
            "geen tickets beschikbaar" not in text
            and (
                "camping chill" in text
                or "camping a" in text
            )
        )

        if available and not last_available:
            send_message(
                "🚨 PUKKELPOP ALERT! 🚨\n\n"
                "Combi Camping Chill lijkt beschikbaar te zijn!\n\n"
                f"{URL}"
            )

        last_available = available

    except Exception:
        pass

    time.sleep(30)
