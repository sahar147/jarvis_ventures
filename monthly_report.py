import sqlite3
import requests
import json
from datetime import datetime, timezone, timedelta
from requests.auth import HTTPBasicAuth
import calendar

TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
DB_PATH = "/freqtrade/user_data/tradesv3.sqlite"
API_URL = "http://localhost:8080/api/v1"
TRADE_COUNT_FILE = "/freqtrade/user_data/trade_count.json"

def get_api_auth():
    with open('/freqtrade/user_data/config.json') as f:
        config = json.load(f)
    return HTTPBasicAuth(config['api_server']['username'], config['api_server']['password'])

def get_current_balance():
    try:
        resp = requests.get(f"{API_URL}/balance", auth=get_api_auth(), timeout=10)
        return float(resp.json()['total'])
    except Exception as e:
        print(f"[Balance] Error: {e}")
        return None

def send_telegram(pesan, pin=False):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    resp = requests.post(url, json={"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"}, timeout=10)
    data = resp.json()
    if resp.status_code == 200:
        print("[Telegram] Terkirim!")
        if pin:
            msg_id = data["result"]["message_id"]
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/pinChatMessage",
                json={"chat_id": CHAT_ID, "message_id": msg_id, "disable_notification": False},
                timeout=10
            )
            print("[Telegram] Di-pin!")
    else:
        print(f"[Telegram] Gagal: {data}")

def get_monthly_stats(year, month):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    month_start = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    month_end = f"{year}-{month:02d}-{last_day}"

    cur.execute("""
        SELECT pair, close_profit_abs, close_profit, close_rate, open_rate,
               is_short, open_date, close_date, enter_tag
        FROM trades
        WHERE is_open=0 AND exit_reason NOT LIKE 'smart_exit%'
        AND close_date >= ?
        AND exit_reason NOT LIKE 'smart_exit%' AND close_date <= ?
        ORDER BY close_date DESC
    """, (month_start, month_end + " 23:59:59"))
    trades = cur.fetchall()

    cur.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN close_profit_abs > 0 THEN 1 ELSE 0 END) as wins,
               SUM(CASE WHEN close_profit_abs <= 0 THEN 1 ELSE 0 END) as losses,
               SUM(close_profit_abs) as total_pnl
        FROM trades
        WHERE is_open=0 AND exit_reason NOT LIKE 'smart_exit%'
        AND close_date >= ?
        AND exit_reason NOT LIKE 'smart_exit%' AND close_date <= ?
    """, (month_start, month_end + " 23:59:59"))
    stats = cur.fetchone()
    conn.close()
    return trades, stats

def send_monthly_report():
    today = datetime.now(timezone.utc)
    # Rekap bulan lalu
    if today.month == 1:
        month = 12
        year = today.year - 1
    else:
        month = today.month - 1
        year = today.year

    month_name = datetime(year, month, 1).strftime("%B %Y")
    trades, stats = get_monthly_stats(year, month)

    total = stats[0] or 0
    wins = stats[1] or 0
    losses = stats[2] or 0
    total_pnl = stats[3] or 0.0
    winrate = (wins / total * 100) if total > 0 else 0
    pnl_emoji = "🟢" if total_pnl >= 0 else "🔴"
    pnl_sign = "+" if total_pnl >= 0 else ""
    balance = get_current_balance()
    balance_str = f"`{balance:.2f} USDT`" if balance else "_N/A_"

    # Best pair bulan ini
    best_trade = ""
    worst_trade = ""
    if trades:
        sorted_trades = sorted(trades, key=lambda x: x[1], reverse=True)
        best = sorted_trades[0]
        worst = sorted_trades[-1]
        best_pct = best[2] * 100 / 10
        worst_pct = worst[2] * 100 / 10
        best_trade = f"  🏆 Best: `{best[0]}` → `{best_pct:+.2f}%`\n"
        worst_trade = f"  💀 Worst: `{worst[0]}` → `{worst_pct:+.2f}%`\n"

    # Detail per pair (groupby pair)
    pair_summary = {}
    for t in trades:
        pair = t[0]
        pnl = t[1]
        if pair not in pair_summary:
            pair_summary[pair] = {"pnl": 0, "count": 0, "wins": 0}
        pair_summary[pair]["pnl"] += pnl
        pair_summary[pair]["count"] += 1
        if pnl > 0:
            pair_summary[pair]["wins"] += 1

    pair_detail = ""
    for pair, data in sorted(pair_summary.items(), key=lambda x: x[1]["pnl"], reverse=True):
        emoji = "✅" if data["pnl"] > 0 else "❌"
        pair_detail += f"  {emoji} `{pair}` — {data['wins']}/{data['count']} win | `{data['pnl']:+.4f} USDT`\n"

    pesan = (
        f"📅 *MONTHLY REPORT — JARVIS x BADUT KOTA*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🗓 *Periode:* `{month_name}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📈 *Performa Bulan Ini:*\n"
        f"  • Total Trade: `{total}`\n"
        f"  • Win: `{wins}` ✅\n"
        f"  • Loss: `{losses}` ❌\n"
        f"  • Winrate: `{winrate:.1f}%`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Total PnL:* {pnl_emoji} `{pnl_sign}{total_pnl:.4f} USDT`\n"
        f"💼 *Saldo Sekarang:* {balance_str}\n"
        f"{best_trade}"
        f"{worst_trade}"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Performa Per Pair:*\n"
        f"{pair_detail if pair_detail else '  _Tidak ada trade_'}"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🤖 *Jarvis* — _AI Trading Bot_\n"
        f"🎪 *Badut Kota* — _@badutkota147_"
    )
    send_telegram(pesan, pin=True)

def send_hall_of_fame():
    today = datetime.now(timezone.utc)
    if today.month == 1:
        month = 12
        year = today.year - 1
    else:
        month = today.month - 1
        year = today.year

    month_name = datetime(year, month, 1).strftime("%B %Y")
    trades, _ = get_monthly_stats(year, month)

    if not trades:
        print("[HoF] Tidak ada trade bulan ini")
        return

    # Trade dengan profit tertinggi
    best = max(trades, key=lambda x: x[1])
    pair = best[0]
    profit_abs = best[1]
    profit_ratio = best[2]
    close_rate = best[3]
    open_rate = best[4]
    is_short = best[5]
    open_date = best[6]
    close_date = best[7]

    arah = "SHORT" if is_short else "LONG"
    pct_display = profit_ratio * 100 / 10
    pct_modal = profit_ratio * 100

    # Hitung durasi
    try:
        open_dt = datetime.strptime(open_date[:19], "%Y-%m-%d %H:%M:%S")
        close_dt = datetime.strptime(close_date[:19], "%Y-%m-%d %H:%M:%S")
        durasi = close_dt - open_dt
        hours = int(durasi.total_seconds() // 3600)
        minutes = int((durasi.total_seconds() % 3600) // 60)
        durasi_str = f"{hours}j {minutes}m"
    except:
        durasi_str = "N/A"

    pesan = (
        f"🏆 *HALL OF FAME — {month_name}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🥇 *Trade Terbaik Bulan Ini!*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📌 *Pair:* `{pair}`\n"
        f"📊 *Arah:* `{arah}`\n"
        f"💰 *Entry:* `{open_rate:.4f} USDT`\n"
        f"🏁 *Exit:* `{close_rate:.4f} USDT`\n"
        f"⏱ *Durasi:* `{durasi_str}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✅ *Profit:* `+{pct_display:.2f}%` harga | `+{pct_modal:.2f}%` modal\n"
        f"💵 *PnL:* `+{profit_abs:.4f} USDT`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🤖 *Jarvis* — _AI Trading Bot_\n"
        f"🎪 *Badut Kota* — _@badutkota147_"
    )
    send_telegram(pesan)

def get_trade_count():
    try:
        with open(TRADE_COUNT_FILE) as f:
            return json.load(f)
    except:
        return {"total": 0, "last_notif": 0}

def save_trade_count(data):
    with open(TRADE_COUNT_FILE, 'w') as f:
        json.dump(data, f)

def check_winrate_tracker():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*), SUM(CASE WHEN close_profit_abs > 0 THEN 1 ELSE 0 END) FROM trades WHERE is_open=0 AND exit_reason NOT LIKE 'smart_exit%'")
    row = cur.fetchone()
    conn.close()

    total = row[0] or 0
    wins = row[1] or 0
    winrate = (wins / total * 100) if total > 0 else 0

    data = get_trade_count()
    last_notif = data.get("last_notif", 0)

    # Kirim setiap kelipatan 50
    if total >= last_notif + 50:
        losses = total - wins
        pnl_emoji = "🟢" if winrate >= 50 else "🔴"

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT SUM(close_profit_abs) FROM trades WHERE is_open=0 AND exit_reason NOT LIKE 'smart_exit%'")
        total_pnl = cur.fetchone()[0] or 0
        conn.close()

        pnl_sign = "+" if total_pnl >= 0 else ""

        pesan = (
            f"📊 *WINRATE TRACKER — JARVIS x BADUT KOTA*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *Milestone: {total} Trade!*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"  • Total Trade: `{total}`\n"
            f"  • Win: `{wins}` ✅\n"
            f"  • Loss: `{losses}` ❌\n"
            f"  • Winrate: {pnl_emoji} `{winrate:.1f}%`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💰 *Total PnL:* `{pnl_sign}{total_pnl:.4f} USDT`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🤖 *Jarvis* — _AI Trading Bot_\n"
            f"🎪 *Badut Kota* — _@badutkota147_"
        )
        send_telegram(pesan)
        save_trade_count({"total": total, "last_notif": total})
        print(f"[Winrate] Notif terkirim! Total: {total} trade")
    else:
        print(f"[Winrate] Total: {total} trade | Next notif: {last_notif + 50} trade")

if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode == "monthly":
        send_monthly_report()
        send_hall_of_fame()
    elif mode == "winrate":
        check_winrate_tracker()
    else:
        send_monthly_report()
        send_hall_of_fame()
        check_winrate_tracker()
