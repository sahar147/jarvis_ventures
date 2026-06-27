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

def send_telegram(pesan, pin=False):
    r = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"},
        timeout=10
    )
    if r.status_code == 200 and pin:
        msg_id = r.json()["result"]["message_id"]
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/pinChatMessage",
            json={"chat_id": CHAT_ID, "message_id": msg_id, "disable_notification": False},
            timeout=10
        )
        print("[Report] Di-pin!")
    return r

def send_chart(trades_all, balance):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        import io

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT close_date, close_profit_abs FROM trades
            WHERE is_open=0 ORDER BY close_date ASC
        """)
        rows = cur.fetchall()
        conn.close()

        if len(rows) < 2:
            return

        b = balance
        for r in reversed(rows):
            b -= r[1]

        balances = [b]
        dates = [datetime.fromisoformat(rows[0][0].replace("+00:00", ""))]
        for r in rows:
            b += r[1]
            balances.append(b)
            dates.append(datetime.fromisoformat(r[0].replace("+00:00", "")))

        fig, ax = plt.subplots(figsize=(10, 4))
        fig.patch.set_facecolor("#1a1a2e")
        ax.set_facecolor("#16213e")
        color = "#00ff88" if balances[-1] >= balances[0] else "#ff4444"
        ax.plot(dates, balances, color=color, linewidth=2)
        ax.fill_between(dates, balances, balances[0], alpha=0.2, color=color)
        ax.set_title("Equity Curve — Jarvis Ventures", color="white", fontsize=13)
        ax.tick_params(colors="white")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
        for spine in ax.spines.values():
            spine.set_edgecolor("#333366")
        ax.grid(True, alpha=0.2, color="white")

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
        buf.seek(0)
        plt.close()

        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
            data={"chat_id": CHAT_ID},
            files={"photo": ("equity.png", buf, "image/png")},
            timeout=15
        )
        print("[Chart] Terkirim!")
    except Exception as e:
        print(f"[Chart] Error: {e}")

def send_daily_report():
    today = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    today_str = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%d %B %Y")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Trade hari ini
    cur.execute("""
        SELECT pair, close_profit_abs, close_profit, close_rate, open_rate,
               is_short, close_date, enter_tag, exit_reason
        FROM trades WHERE is_open=0 AND close_date LIKE ?
        ORDER BY close_date DESC
    """, (f"{today}%",))
    trades = cur.fetchall()

    # Statistik keseluruhan
    cur.execute("""
        SELECT COUNT(*), SUM(CASE WHEN close_profit_abs>0 THEN 1 ELSE 0 END),
               SUM(CASE WHEN close_profit_abs<=0 THEN 1 ELSE 0 END),
               SUM(close_profit_abs), AVG(JULIANDAY(close_date)-JULIANDAY(open_date))*86400,
               MAX(close_profit), MIN(close_profit)
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

    # Global stats
    g_total = stats[0] or 0
    g_wins = stats[1] or 0
    g_losses = stats[2] or 0
    g_pnl = stats[3] or 0
    g_wr = (g_wins/g_total*100) if g_total > 0 else 0
    g_avg_dur = str(timedelta(seconds=int(stats[4] or 0)))
    pf = 0

    # Detail trades
    detail = ""
    for t in trades:
        emoji = "✅" if t[1] > 0 else "❌"
        arah = "SHORT" if t[5] else "LONG"
        pct = t[2] * 10
        sign = "+" if pct >= 0 else ""
        detail += f"{emoji} {t[0]} {arah} -> {sign}{pct:.2f}%\n"

    # Best/worst
    best = max(trades, key=lambda x: x[1]) if trades else None
    worst = min(trades, key=lambda x: x[1]) if trades else None

    pesan = (
        f"📊 *DAILY REPORT — JARVIS x BADUT KOTA*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📅 *Tanggal:* `{today_str}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📈 *Performa Hari Ini:*\n"
        f"  • Total Trade: `{total}`\n"
        f"  • Win: `{wins}` ✅\n"
        f"  • Loss: `{losses}` ❌\n"
        f"  • Winrate: `{winrate:.1f}%`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Total PnL Hari Ini:* {pnl_emoji} `{pnl_sign}{total_pnl:.4f} USDT`\n"
        f"💼 *Saldo Sekarang:* `{balance:.2f} USDT`\n"
    )

    if best:
        pesan += f"🏆 *Best:* `{best[0]}` -> `{best[2]*10:+.2f}%`\n"
    if worst:
        pesan += f"💀 *Worst:* `{worst[0]}` -> `{worst[2]*10:+.2f}%`\n"

    if detail:
        pesan += f"━━━━━━━━━━━━━━━━━━\n📋 *Detail Trade Hari Ini:*\n{detail}"

    pesan += (
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Statistik Keseluruhan:*\n"
        f"  • Total Trade: `{g_total}`\n"
        f"  • Win/Loss: `{g_wins}/{g_losses}`\n"
        f"  • Winrate: `{g_wr:.1f}%`\n"
        f"  • Avg Duration: `{g_avg_dur}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🤖 *Jarvis* — _AI Trading Bot_\n"
        f"🎪 *Badut Kota* — _@badutkota147_\n"
        f"👤 *Owner:* _Pakdendam_\n"
        f"📦 *Repo:* [jarvis_ventures](https://github.com/sahar147/jarvis_ventures)"
    )

    send_chart(trades, balance)
    r = send_telegram(pesan, pin=True)
    if r.status_code == 200:
        print("[Report] Terkirim!")
    else:
        print(f"[Report] Gagal: {r.text}")

if __name__ == "__main__":
    send_daily_report()
