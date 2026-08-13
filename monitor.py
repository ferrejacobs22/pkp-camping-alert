import os
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

URL = "https://tickets.pukkelpop.be/nl/meetup/demand/?type=combi&camping=a&price=all"

def send_message(message):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=10
    )

response = requests.get(URL, timeout=15)
text = response.text.lower()

if "geen tickets beschikbaar" not in text:
    send_message(
        "🚨 PUKKELPOP ALERT 🚨\n\n"
        "Er lijkt iets beschikbaar te zijn voor Combi Camping Chill!\n\n"
        + URL
    )
else:
    print("Geen Combi Camping Chill beschikbaar.")
