import json, requests
from datetime import datetime, timezone

TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
STATUS_FILE = "/freqtrade/user_data/session.log"

def send_telegram(pesan):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"},
        timeout=10
    )

hour = datetime.now(timezone.utc).hour
wib = (hour + 7) % 24

try:
    with open(STATUS_FILE) as f:
        last = f.read().strip()
except:
    last = ""

if 3 <= hour < 21:
    status = "active"
else:
    status = "skip"

if last != status:
    with open(STATUS_FILE, "w") as f:
        f.write(status)
    if status == "active":
        pesan = (
            f"🟢 *SESI TRADING AKTIF — JARVIS*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⏰ *Waktu:* `{hour:02d}:00 UTC` | `{wib:02d}:00 WIB`\n"
            f"📊 *Status:* Bot aktif mencari sinyal\n"
            f"🕐 *Sesi aktif:* `10.00 - 04.00 WIB`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🤖 *Jarvis* — _AI Trading Bot_\n"
            f"🎪 *Badut Kota* — _@badutkota147_"
        )
    else:
        pesan = (
            f"🔴 *SESI SKIP ENTRY — JARVIS*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⏰ *Waktu:* `{hour:02d}:00 UTC` | `{wib:02d}:00 WIB`\n"
            f"📊 *Status:* Bot standby, sesi asia sepi mendingan tidur dulu sayangi modal\n"
            f"🕐 *Sesi skip:* `04.00 - 10.00 WIB`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🤖 *Jarvis* — _AI Trading Bot_\n"
            f"🎪 *Badut Kota* — _@badutkota147_"
        )
    send_telegram(pesan)
    print(f"Notif terkirim: {status}")
else:
    print(f"Tidak ada perubahan sesi: {status}")
