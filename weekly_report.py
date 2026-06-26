import sqlite3
import requests
import json
import os
from datetime import datetime, timezone, timedelta
from requests.auth import HTTPBasicAuth

TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
DB_PATH = "/freqtrade/user_data/tradesv3.sqlite"
API_URL = "http://localhost:8080/api/v1"
PEAK_FILE = "/freqtrade/user_data/peak_balance.json"

def get_api_auth():
    with open('/freqtrade/user_data/config.json') as f:
        config = json.load(f)
    username = config['api_server']['username']
    password = config['api_server']['password']
    return HTTPBasicAuth(username, password)

def get_current_balance():
    try:
        auth = get_api_auth()
        resp = requests.get(f"{API_URL}/balance", auth=auth, timeout=10)
        data = resp.json()
        return float(data['total'])
    except Exception as e:
        print(f"[Balance] Error: {e}")
        return None

def get_peak_balance():
    if os.path.exists(PEAK_FILE):
        with open(PEAK_FILE) as f:
            data = json.load(f)
        return data.get('peak', 0)
    return 0

def save_peak_balance(peak):
    with open(PEAK_FILE, 'w') as f:
        json.dump({'peak': peak, 'updated': datetime.now(timezone.utc).isoformat()}, f)

def check_drawdown():
    current = get_current_balance()
    if current is None:
        return
    peak = get_peak_balance()
    if current > peak:
        save_peak_balance(current)
        print(f"[Drawdown] Peak baru: {current:.2f} USDT")
        return
    if peak == 0:
        save_peak_balance(current)
        return
    drawdown_pct = (peak - current) / peak * 100
    # Konversi 10:1 (10% modal = 1% harga)
    drawdown_display = drawdown_pct / 10
    print(f"[Drawdown] Current: {current:.2f} | Peak: {peak:.2f} | DD: {drawdown_pct:.2f}% modal ({drawdown_display:.2f}% harga)")
    if drawdown_pct >= 10:
        send_drawdown_alert(current, peak, drawdown_pct, drawdown_display)

def send_drawdown_alert(current, peak, drawdown_pct, drawdown_display):
    waktu = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pesan = (
        f"⚠️ *DRAWDOWN ALERT — JARVIS*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📉 *Drawdown:* `-{drawdown_pct:.1f}% modal` (`-{drawdown_display:.1f}% harga`)\n"
        f"🏔 *Peak Saldo:* `{peak:.2f} USDT`\n"
        f"💰 *Saldo Sekarang:* `{current:.2f} USDT`\n"
        f"📊 *Selisih:* `-{peak - current:.2f} USDT`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🕐 *Waktu:* `{waktu}`\n"
        f"🤖 *Jarvis* — _AI Trading Bot_\n"
        f"🎪 *Badut Kota* — _@badutkota147_\n"
        f"👤 *Owner:* _Pakdendam_\n"
        f"📦 *Repo:* [jarvis\_ventures](https://github.com/sahar147/jarvis_ventures)"
    )
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    resp = requests.post(url, json={"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"}, timeout=10)
    if resp.status_code == 200:
        print("[Drawdown] Alert terkirim!")
    else:
        print(f"[Drawdown] Gagal: {resp.text}")

def get_weekly_stats():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    today = datetime.now(timezone.utc)
    week_ago = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    cur.execute("""
        SELECT pair, close_profit_abs, close_profit, close_rate, open_rate,
               is_short, close_date, enter_tag
        FROM trades
        WHERE is_open=0 AND exit_reason NOT LIKE 'smart_exit%'
        AND close_date >= ?
        AND exit_reason NOT LIKE 'smart_exit%'
        ORDER BY close_date DESC
    """, (week_ago,))
    trades = cur.fetchall()
    cur.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN close_profit_abs > 0 THEN 1 ELSE 0 END) as wins,
               SUM(CASE WHEN close_profit_abs <= 0 THEN 1 ELSE 0 END) as losses,
               SUM(close_profit_abs) as total_pnl
        FROM trades
        WHERE is_open=0 AND exit_reason NOT LIKE 'smart_exit%'
        AND close_date >= ?
        AND exit_reason NOT LIKE 'smart_exit%'
    """, (week_ago,))
    stats = cur.fetchone()
    conn.close()
    return trades, stats

def send_weekly_report():
    trades, stats = get_weekly_stats()
    today = datetime.now(timezone.utc)
    week_ago = (today - timedelta(days=7)).strftime("%d %b")
    today_str = today.strftime("%d %b %Y")
    total = stats[0] or 0
    wins = stats[1] or 0
    losses = stats[2] or 0
    total_pnl = stats[3] or 0.0
    winrate = (wins / total * 100) if total > 0 else 0
    pnl_emoji = "🟢" if total_pnl >= 0 else "🔴"
    pnl_sign = "+" if total_pnl >= 0 else ""
    current_balance = get_current_balance()
    balance_str = f"`{current_balance:.2f} USDT`" if current_balance else "_N/A_"

    if total == 0:
        detail = "  _Tidak ada trade minggu ini_"
        best_trade = ""
        worst_trade = ""
    else:
        detail = ""
        for t in trades:
            pair, profit_abs, profit_ratio, close_rate, open_rate, is_short, close_date, tag = t
            arah = "SHORT" if is_short else "LONG"
            hasil = "✅" if profit_abs > 0 else "❌"
            # Konversi 10:1
            pct = profit_ratio * 100 / 10
            detail += f"  {hasil} `{pair}` {arah} → `{pct:+.2f}%`\n"
        sorted_trades = sorted(trades, key=lambda x: x[1], reverse=True)
        best = sorted_trades[0]
        worst = sorted_trades[-1]
        best_pct = best[2] * 100 / 10
        worst_pct = worst[2] * 100 / 10
        best_trade = f"  🏆 Best: `{best[0]}` → `{best_pct:+.2f}%`\n"
        worst_trade = f"  💀 Worst: `{worst[0]}` → `{worst_pct:+.2f}%`\n"

    pesan = (
        f"📅 *WEEKLY REPORT — JARVIS x BADUT KOTA*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📆 *Periode:* `{week_ago} — {today_str}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📈 *Performa Minggu Ini:*\n"
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
        f"📋 *Detail Trade:*\n"
        f"{detail}"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🤖 *Jarvis* — _AI Trading Bot_\n"
        f"🎪 *Badut Kota* — _@badutkota147_\n"
        f"👤 *Owner:* _Pakdendam_\n"
        f"📦 *Repo:* [jarvis\_ventures](https://github.com/sahar147/jarvis_ventures)"
    )

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    resp = requests.post(url, json={"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"}, timeout=10)
    data = resp.json()
    if resp.status_code == 200:
        print("[Weekly] Terkirim!")
        msg_id = data["result"]["message_id"]
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/pinChatMessage",
            json={"chat_id": CHAT_ID, "message_id": msg_id, "disable_notification": False},
            timeout=10
        )
        print("[Weekly] Di-pin!")
    else:
        print(f"[Weekly] Gagal: {data}")

def send_equity_curve():
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from io import BytesIO

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        today = datetime.now(timezone.utc)
        month_ago = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        cur.execute("""
            SELECT close_date, SUM(close_profit_abs) OVER (ORDER BY close_date) as cumulative_pnl
            FROM trades
            WHERE is_open=0 AND exit_reason NOT LIKE 'smart_exit%' AND close_date >= ?
        AND exit_reason NOT LIKE 'smart_exit%'
            ORDER BY close_date
        """, (month_ago,))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            print("[Equity] Tidak ada data 30 hari")
            return

        dates = [datetime.strptime(r[0][:19], "%Y-%m-%d %H:%M:%S") for r in rows]
        pnl = [r[1] for r in rows]

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(dates, pnl, color='#00C853', linewidth=2)
        ax.fill_between(dates, pnl, alpha=0.1, color='#00C853')
        ax.set_title('📈 Equity Curve — Jarvis x Badut Kota (30 Hari)', fontsize=14, pad=15)
        ax.set_ylabel('Cumulative PnL (USDT)')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator())
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        plt.xticks(rotation=45)
        plt.tight_layout()

        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150)
        buf.seek(0)
        plt.close()

        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        caption = (
            f"📈 *EQUITY CURVE — 30 Hari Terakhir*\n"
            f"🤖 *Jarvis* — _AI Trading Bot_\n"
            f"🎪 *Badut Kota* — _@badutkota147_"
        )
        resp = requests.post(url, data={"chat_id": CHAT_ID, "caption": caption, "parse_mode": "Markdown"},
                           files={"photo": ("equity.png", buf, "image/png")}, timeout=30)
        if resp.status_code == 200:
            print("[Equity] Grafik terkirim!")
        else:
            print(f"[Equity] Gagal: {resp.text}")
    except ImportError:
        print("[Equity] matplotlib tidak tersedia, skip grafik")
    except Exception as e:
        print(f"[Equity] Error: {e}")

if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode == "drawdown":
        check_drawdown()
    elif mode == "weekly":
        send_weekly_report()
        send_equity_curve()
    else:
        send_weekly_report()
        send_equity_curve()
