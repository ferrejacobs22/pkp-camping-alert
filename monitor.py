import os
import time
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

CAMPING_URL = "https://tickets.pukkelpop.be/nl/meetup/demand/?type=combi&camping=a&price=all"
SATURDAY_URL = "https://tickets.pukkelpop.be/nl/meetup/demand/?type=day2&camping=n&price=all#tickets"

CHECK_INTERVAL = 5
HEARTBEAT_INTERVAL = 600

def send_telegram(message):
try:
response = requests.post(
f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
data={
"chat_id": CHAT_ID,
"text": message
},
timeout=10
)

```
    print(
        f"Telegram: {response.status_code}",
        flush=True
    )

except Exception as e:
    print(
        f"Telegram fout: {e}",
        flush=True
    )
```

def check_ticket(page, name, url):
try:
print(
f"🔎 {name} controleren...",
flush=True
)

```
    page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=30000
    )

    try:
        page.wait_for_selector(
            "body",
            timeout=5000
        )
    except Exception:
        pass

    text = page.locator(
        "body"
    ).inner_text().lower()

    available = "geen tickets beschikbaar" not in text

    print(
        f"{name}: Beschikbaar = {available}",
        flush=True
    )

    return available

except Exception as e:
    print(
        f"⚠️ Fout bij {name}: {e}",
        flush=True
    )

    return False
```

print(
"🌐 PKP Ticket Monitor gestart",
flush=True
)

print(
"🏕️ Camping A + 🎟️ zaterdag worden gecontroleerd",
flush=True
)

last_camping = False
last_saturday = False
last_heartbeat = time.monotonic()

with sync_playwright() as p:

```
print(
    "🚀 Chromium starten...",
    flush=True
)

browser = p.chromium.launch(
    headless=True,
    args=[
        "--no-sandbox",
        "--disable-dev-shm-usage"
    ]
)

page = browser.new_page()

while True:

    try:

        camping_available = check_ticket(
            page,
            "CAMPING A",
            CAMPING_URL
        )

        saturday_available = check_ticket(
            page,
            "ZATERDAG",
            SATURDAY_URL
        )

        if camping_available and not last_camping:

            send_telegram(
                "🚨 CAMPING A TICKET BESCHIKBAAR! 🚨\n\n"
                f"{CAMPING_URL}"
            )

        if saturday_available and not last_saturday:

            send_telegram(
                "🚨 ZATERDAG TICKET BESCHIKBAAR! 🚨\n\n"
                f"{SATURDAY_URL}"
            )

        last_camping = camping_available
        last_saturday = saturday_available

        if time.monotonic() - last_heartbeat >= HEARTBEAT_INTERVAL:

            now = datetime.now().strftime(
                "%d-%m-%Y %H:%M:%S"
            )

            send_telegram(
                "🟢 PKP MONITOR ACTIEF\n\n"
                f"Heartbeat: {now}\n"
                "Camping A + zaterdag worden gecontroleerd."
            )

            last_heartbeat = time.monotonic()

    except Exception as e:

        print(
            f"⚠️ Algemene fout: {e}",
            flush=True
        )

    time.sleep(CHECK_INTERVAL)
```
