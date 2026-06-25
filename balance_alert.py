import requests
import json
import os
from requests.auth import HTTPBasicAuth

TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
API_URL = "http://localhost:8080/api/v1"
MIN_BALANCE = 5.0
FLAG_FILE = "/freqtrade/user_data/balance_alert_sent.flag"

def get_api_auth():
    with open('/freqtrade/user_data/config.json') as f:
        config = json.load(f)
    return HTTPBasicAuth(config['api_server']['username'], config['api_server']['password'])

def check_balance():
    try:
        resp = requests.get(f"{API_URL}/balance", auth=get_api_auth(), timeout=10)
        balance = float(resp.json()['total'])

        if balance <= MIN_BALANCE:
            # Cek apakah sudah pernah kirim notif
            if os.path.exists(FLAG_FILE):
                print(f"[Alert] Saldo {balance:.2f} USDT - notif sudah terkirim sebelumnya, skip!")
                return

            pesan = (
                f"⚠️ *SALDO MINIMUM — JARVIS*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💼 *Saldo:* `{balance:.2f} USDT`\n"
                f"⛔ Saldo tidak cukup untuk entry!\n"
                f"💡 Deposit diperlukan!\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🤖 *Jarvis* — _AI Trading Bot_\n"
                f"🎪 *Badut Kota* — _@badutkota147_"
            )
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(url, json={"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"}, timeout=10)
            
            # Buat flag supaya tidak spam
            open(FLAG_FILE, 'w').close()
            print(f"[Alert] Saldo {balance:.2f} USDT - notif terkirim!")

        else:
            # Saldo sudah cukup lagi, hapus flag
            if os.path.exists(FLAG_FILE):
                os.remove(FLAG_FILE)
                print(f"[Alert] Saldo {balance:.2f} USDT - flag dihapus, saldo aman!")
            else:
                print(f"[Alert] Saldo {balance:.2f} USDT - aman!")

    except Exception as e:
        print(f"[Alert] Error: {e}")

if __name__ == "__main__":
    check_balance()
