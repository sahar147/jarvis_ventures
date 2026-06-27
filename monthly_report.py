import sqlite3, requests, json
from datetime import datetime, timezone, timedelta
from requests.auth import HTTPBasicAuth

TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
DB_PATH = "/freqtrade/user_data/tradesv3.sqlite"
API_URL = "http://localhost:8080/api/v1"

def get_auth():
    with open('/freqtrade/user_data/config.json') as f:
        c = json.load(f)
    return HTTPBasicAuth(c['api_server']['username'], c['api_server']['password'])

def get_balance():
    try:
        r = requests.get(f"{API_URL}/balance", auth=get_auth(), timeout=10)
        return float(r.json()['total'])
    except:
        return 0.0

def send_telegram(pesan):
    r = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"},
        timeout=10
    )
    return r

def send_monthly_report():
    now = datetime.now(timezone.utc)
    bulan = now.strftime("%B %Y")
    start = now.replace(day=1).strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT pair, close_profit_abs, close_profit, close_rate, open_rate,
               is_short, close_date
        FROM trades WHERE is_open=0 AND close_date >= ?
        ORDER BY close_date DESC
    """, (start,))
    trades = cur.fetchall()

    cur.execute("""
        SELECT COUNT(*), SUM(CASE WHEN close_profit_abs>0 THEN 1 ELSE 0 END),
               SUM(CASE WHEN close_profit_abs<=0 THEN 1 ELSE 0 END),
               SUM(close_profit_abs), AVG(JULIANDAY(close_date)-JULIANDAY(open_date))*86400,
               MAX(close_profit_abs), MIN(close_profit_abs)
        FROM trades WHERE is_open=0
    """)
    stats = cur.fetchone()
    conn.close()

    balance = get_balance()
    total = len(trades)
    wins = sum(1 for t in trades if t[1] > 0)
    losses = total - wins
    winrate = (wins/total*100) if total > 0 else 0
    total_pnl = sum(t[1] for t in trades)
    pnl_emoji = "🟢" if total_pnl >= 0 else "🔴"
    pnl_sign = "+" if total_pnl >= 0 else ""

    g_total = stats[0] or 0
    g_wins = stats[1] or 0
    g_losses = stats[2] or 0
    g_pnl = stats[3] or 0
    g_wr = (g_wins/g_total*100) if g_total > 0 else 0
    g_avg_dur = str(timedelta(seconds=int(stats[4] or 0)))

    best = max(trades, key=lambda x: x[1]) if trades else None
    worst = min(trades, key=lambda x: x[1]) if trades else None

    pesan = (
        f"📊 *MONTHLY REPORT — JARVIS x BADUT KOTA*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📅 *Bulan:* `{bulan}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📈 *Performa Bulan Ini:*\n"
        f"  • Total Trade: `{total}`\n"
        f"  • Win: `{wins}` ✅\n"
        f"  • Loss: `{losses}` ❌\n"
        f"  • Winrate: `{winrate:.1f}%`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Total PnL Bulan Ini:* {pnl_emoji} `{pnl_sign}{total_pnl:.4f} USDT`\n"
        f"💼 *Saldo Sekarang:* `{balance:.2f} USDT`\n"
    )

    if best:
        pesan += f"🏆 *Best:* `{best[0]}` -> `{best[2]*10:+.2f}%`\n"
    if worst:
        pesan += f"💀 *Worst:* `{worst[0]}` -> `{worst[2]*10:+.2f}%`\n"

    pesan += (
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Statistik Keseluruhan:*\n"
        f"  • Total Trade: `{g_total}`\n"
        f"  • Win/Loss: `{g_wins}/{g_losses}`\n"
        f"  • Winrate: `{g_wr:.1f}%`\n"
        f"  • Avg Duration: `{g_avg_dur}`\n"
        f"  • PnL Total: `{g_pnl:+.4f} USDT`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🤖 *Jarvis* — _AI Trading Bot_\n"
        f"🎪 *Badut Kota* — _@badutkota147_\n"
        f"👤 *Owner:* _Pakdendam_\n"
        f"📦 *Repo:* [jarvis_ventures](https://github.com/sahar147/jarvis_ventures)"
    )

    r = send_telegram(pesan)
    if r.status_code == 200:
        print("[Monthly] Terkirim!")
    else:
        print(f"[Monthly] Gagal: {r.text}")

if __name__ == "__main__":
    send_monthly_report()
