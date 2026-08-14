import os
import time
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_BOT_TOKEN = os.environ[“TELEGRAM_BOT_TOKEN”]
TELEGRAM_CHAT_ID = os.environ[“TELEGRAM_CHAT_ID”]

TICKETS = {
“Zaterdag zonder camping”: {
“url”: “https://tickets.pukkelpop.be/nl/meetup/demand/?type=day2&camping=n&price=all#tickets”,
“emoji”: “🎟️”,
},
“Combi + Camping Chill”: {
“url”: “https://tickets.pukkelpop.be/nl/meetup/demand/?type=combi&camping=a&price=all#tickets”,
“emoji”: “🏕️”,
},
}

Hoe lang wachten tussen volledige controles

CHECK_INTERVAL = 2

Om geheugen te besparen wordt Chromium regelmatig volledig opnieuw gestart

BROWSER_RESTART_EVERY = 20

Opnieuw een Telegrammelding sturen zolang tickets beschikbaar zijn

ALERT_REPEAT_SECONDS = 10

def send_telegram(message):
url = f”https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage”

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
print(f”🔎 Controle: {name}”, flush=True)

try:
    page.goto(
        info["url"],
        wait_until="domcontentloaded",
        timeout=15000,
    )
    # Even wachten zodat de ticketinformatie geladen kan worden
    page.wait_for_timeout(1000)
    text = page.locator("body").inner_text().lower()
    unavailable_phrases = [
        "geen tickets beschikbaar",
        "geen tickets",
        "uitverkocht",
        "sold out",
        "niet beschikbaar",
    ]
    for phrase in unavailable_phrases:
        if phrase in text:
            print(f"❌ {name}: geen tickets", flush=True)
            return False
    print(f"🚨 {name}: MOGELIJK BESCHIKBAAR!", flush=True)
    return True
except Exception as e:
    print(f"⚠️ Fout bij {name}: {e}", flush=True)
    return None

def create_browser(p):
print(“🌐 Chromium wordt gestart…”, flush=True)

browser = p.chromium.launch(
    headless=True,
    args=[
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-extensions",
        "--disable-background-networking",
        "--disable-background-timer-throttling",
        "--disable-renderer-backgrounding",
        "--disable-features=Translate,BackForwardCache",
    ],
)
context = browser.new_context(
    java_script_enabled=True,
    service_workers="block",
)
# Blokkeer zware bestanden die we voor deze monitor niet nodig hebben
def block_heavy_resources(route):
    request = route.request
    resource_type = request.resource_type
    if resource_type in [
        "image",
        "media",
        "font",
    ]:
        route.abort()
    else:
        route.continue_()
context.route("**/*", block_heavy_resources)
page = context.new_page()
return browser, context, page

def close_browser(browser, context, page):
try:
page.close()
except Exception:
pass

try:
    context.close()
except Exception:
    pass
try:
    browser.close()
except Exception:
    pass

def main():
print(”================================”, flush=True)
print(“🟢 PKP MONITOR GESTART”, flush=True)
print(”================================”, flush=True)

# Telegram test
try:
    send_telegram(
        "🟢 PKP Monitor is gestart!\n\n"
        "Ik controleer:\n"
        "🎟️ Zaterdag zonder camping\n"
        "🏕️ Combi + Camping Chill\n\n"
        "Controle elke 2 seconden.\n"
        "♻️ Geheugenbesparing actief."
    )
    print("📲 Telegram verbinding OK", flush=True)
except Exception as e:
    print(f"❌ Telegram verbinding mislukt: {e}", flush=True)
last_alert = {
    "Zaterdag zonder camping": 0,
    "Combi + Camping Chill": 0,
}
check_count = 0
with sync_playwright() as p:
    browser = None
    context = None
    page = None
    try:
        browser, context, page = create_browser(p)
        while True:
            # Chromium regelmatig volledig opnieuw starten
            if check_count > 0 and check_count % BROWSER_RESTART_EVERY == 0:
                print(
                    "♻️ Chromium wordt opnieuw gestart om geheugen vrij te maken...",
                    flush=True,
                )
                close_browser(browser, context, page)
                time.sleep(1)
                browser, context, page = create_browser(p)
                print(
                    "✅ Chromium opnieuw gestart",
                    flush=True,
                )
            check_count += 1
            print(
                f"🔄 Controleronde #{check_count}",
                flush=True,
            )
            for name, info in TICKETS.items():
                result = check_ticket(page, name, info)
                # Alleen bij een echte positieve controle melden
                if result is True:
                    now = time.time()
                    # Niet honderden Telegramberichten per seconde sturen.
                    # Zolang het ticket beschikbaar blijft,
                    # komt er elke ALERT_REPEAT_SECONDS een nieuwe melding.
                    if (
                        now - last_alert[name]
                        >= ALERT_REPEAT_SECONDS
                    ):
                        message = (
                            f"{info['emoji']} PKP TICKET BESCHIKBAAR!\n\n"
                            f"🔥 {name}\n\n"
                            f"👉 NU KIJKEN:\n"
                            f"{info['url']}\n\n"
                            f"⚠️ Ticket kan snel verdwijnen!"
                        )
                        try:
                            send_telegram(message)
                            print(
                                f"📲 Telegram ALERT verstuurd: {name}",
                                flush=True,
                            )
                            last_alert[name] = now
                        except Exception as e:
                            print(
                                f"⚠️ Telegram-fout: {e}",
                                flush=True,
                            )
                # Bij geen ticket timer resetten
                elif result is False:
                    last_alert[name] = 0
                # Bij een technische fout niets veranderen
                # zodat een tijdelijke fout geen valse melding veroorzaakt
                else:
                    print(
                        f"⚠️ Controle mislukt voor {name}, "
                        f"volgende controle opnieuw proberen.",
                        flush=True,
                    )
            print(
                f"⏱️ Volgende controle over {CHECK_INTERVAL} seconden...",
                flush=True,
            )
            time.sleep(CHECK_INTERVAL)
    except Exception as e:
        print(
            f"💥 Onverwachte fout in monitor: {e}",
            flush=True,
        )
        try:
            send_telegram(
                "⚠️ PKP Monitor is onverwacht gestopt.\n\n"
                "Render probeert de service automatisch opnieuw te starten."
            )
        except Exception:
            pass
        raise
    finally:
        if browser is not None:
            close_browser(browser, context, page)

if name == “main”:
main()
