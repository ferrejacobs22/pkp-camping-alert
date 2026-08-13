import os
import time
import threading
import requests
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from playwright.sync_api import sync_playwright

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

TICKETS = {
"CAMPING A": "https://tickets.pukkelpop.be/nl/meetup/demand/?type=combi&camping=a&price=all",
"ZATERDAG": "https://tickets.pukkelpop.be/nl/meetup/demand/?type=day2&camping=n&price=all#tickets",
}

CHECK_INTERVAL = 5
HEARTBEAT_INTERVAL = 600

class HealthHandler(BaseHTTPRequestHandler):
def do_GET(self):
self.send_response(200)
self.end_headers()
self.wfile.write(b"PKP Ticket Monitor is running")

```
def log_message(self, format, *args):
    pass
```

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

```
    if response.ok:
        print("Telegram melding verstuurd", flush=True)
    else:
        print(
            f"Telegram fout: {response.status_code} {response.text}",
            flush=True,
        )

except Exception as e:
    print(f"Telegram fout: {e}", flush=True)
```

def send_heartbeat():
now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

```
send_telegram(
    "🟢 PKP MONITOR ACTIEF\n\n"
    f"Heartbeat: {now}\n"
    "Camping A + zaterdag worden gecontroleerd."
)
```

threading.Thread(target=start_server, daemon=True).start()

print("PKP Ticket Monitor gestart", flush=True)

last_available = {
"CAMPING A": False,
"ZATERDAG": False,
}

last_heartbeat = time.monotonic()

with sync_playwright() as p:

```
print("Chromium starten...", flush=True)

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

        if time.monotonic() - last_heartbeat >= HEARTBEAT_INTERVAL:
            send_heartbeat()
            last_heartbeat = time.monotonic()

        for ticket_name, url in TICKETS.items():

            try:

                print(
                    f"Pukkelpop {ticket_name} controleren...",
                    flush=True
                )

                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=30000,
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

                no_tickets = (
                    "geen tickets beschikbaar"
                    in text
                )

                available = not no_tickets

                print(
                    f"{ticket_name}: Beschikbaar = {available}",
                    flush=True
                )

                if available and not last_available[ticket_name]:

                    send_telegram(
                        f"🚨 {ticket_name} TICKET BESCHIKBAAR! 🚨\n\n"
                        "Er lijkt een ticket beschikbaar te zijn.\n\n"
                        f"{url}"
                    )

                last_available[ticket_name] = available

            except Exception as e:

                print(
                    f"Fout bij {ticket_name}: {e}",
                    flush=True
                )

    except Exception as e:

        print(
            f"Algemene fout: {e}",
            flush=True
        )

    time.sleep(CHECK_INTERVAL)
```
