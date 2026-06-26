import sqlite3
import requests
import json
import pandas as pd
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
    return HTTPBasicAuth(config['api_server']['username'], config['api_server']['password'])

def get_current_balance():
    try:
        resp = requests.get(f"{API_URL}/balance", auth=get_api_auth(), timeout=10)
        return float(resp.json()['total'])
    except Exception as e:
        print(f"[Balance] Error: {e}")
        return None

def get_profit_stats():
    try:
        resp = requests.get(f"{API_URL}/profit", auth=get_api_auth(), timeout=10)
        return resp.json()
    except Exception as e:
        print(f"[Profit] Error: {e}")
        return None

def get_market_regime():
    try:
        price_resp = requests.get(
            "https://fapi.binance.com/fapi/v1/ticker/price?symbol=BTCUSDT",
            timeout=10
        )
        btc_price = float(price_resp.json()["price"])
        kline_resp = requests.get(
            "https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=1d&limit=201",
            timeout=10
        )
        klines = kline_resp.json()
        closes = [float(k[4]) for k in klines]
        df = pd.Series(closes)
        ema200 = float(df.ewm(span=200, adjust=False).mean().iloc[-1])
        is_bull = btc_price > ema200
        return btc_price, ema200, is_bull
    except Exception as e:
        print(f"[Regime] Error: {e}")
    return None, None, None

def get_drawdown_info(balance):
    try:
        with open(PEAK_FILE) as f:
            peak_data = json.load(f)
        peak = float(peak_data.get("peak", 0))
        if balance and peak > 0:
            if balance > peak:
                with open(PEAK_FILE, "w") as f:
                    json.dump({"peak": balance, "updated": datetime.now(timezone.utc).isoformat()}, f)
                return None, balance
            drawdown = (peak - balance) / peak * 100
            drawdown_display = drawdown / 10
            return f"⚠️ *Drawdown:* `-{drawdown:.1f}% modal` (`-{drawdown_display:.1f}% harga`) dari peak `{peak:.2f} USDT`\n", peak
    except Exception as e:
        print(f"[Drawdown] Error: {e}")
    return None, None

def send_market_regime():
    btc_price, ema200, is_bull = get_market_regime()
    if btc_price is None:
        print("[Regime] Data tidak tersedia")
        return

    if is_bull:
        regime = "BULL MARKET"
        regime_emoji = "🟢"
        focus = "Jarvis fokus LONG (threshold 4/6)\nSHORT lebih ketat (threshold 5/6)"
    else:
        regime = "BEAR MARKET"
        regime_emoji = "🔴"
        focus = "Jarvis fokus SHORT (threshold 4/6)\nLONG lebih ketat (threshold 5/6)"

    pesan = (
        f"📊 *MARKET REGIME — JARVIS*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"*Kondisi:* {regime_emoji} `{regime}`\n"
        f"💰 *BTC Sekarang:* `{btc_price:,.2f} USDT`\n"
        f"📉 *BTC EMA200 1D:* `{ema200:,.2f} USDT`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📋 *Status Bot:*\n"
        f"`{focus}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🤖 *Jarvis* — _AI Trading Bot_\n"
        f"🎪 *Badut Kota* — _@badutkota147_\n"
        f"📦 *Repo:* github.com/sahar147/jarvis\_ventures"
    )

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    resp = requests.post(url, json={"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"}, timeout=10)
    if resp.status_code == 200:
        print(f"[Regime] Terkirim! {regime_emoji} {regime}")
    else:
        print(f"[Regime] Gagal: {resp.text}")

def get_daily_stats():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    today = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    cur.execute("""
        SELECT pair, close_profit_abs, close_profit, close_rate, open_rate,
               is_short, close_date, enter_tag
        FROM trades
        WHERE is_open=0 AND exit_reason NOT LIKE 'smart_exit%'
        AND close_date LIKE ?
        AND exit_reason NOT LIKE 'smart_exit%'
        ORDER BY close_date DESC
    """, (f"{today}%",))
    trades = cur.fetchall()
    cur.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN close_profit_abs > 0 THEN 1 ELSE 0 END) as wins,
               SUM(CASE WHEN close_profit_abs <= 0 THEN 1 ELSE 0 END) as losses,
               SUM(close_profit_abs) as total_pnl
        FROM trades
        WHERE is_open=0 AND exit_reason NOT LIKE 'smart_exit%'
        AND close_date LIKE ?
        AND exit_reason NOT LIKE 'smart_exit%'
    """, (f"{today}%",))
    stats = cur.fetchone()
    conn.close()
    return trades, stats

def send_daily_report():
    send_market_regime()

    trades, stats = get_daily_stats()
    profit_stats = get_profit_stats()
    today = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%d %B %Y")

    total = stats[0] or 0
    wins = stats[1] or 0
    losses = stats[2] or 0
    total_pnl = stats[3] or 0.0
    winrate = (wins / total * 100) if total > 0 else 0
    pnl_emoji = "🟢" if total_pnl >= 0 else "🔴"
    pnl_sign = "+" if total_pnl >= 0 else ""
    balance = get_current_balance()
    balance_str = f"`{balance:.2f} USDT`" if balance else "_N/A_"

    # Drawdown info
    drawdown_str, peak = get_drawdown_info(balance)
    drawdown_line = drawdown_str if drawdown_str else ""

    if total == 0:
        detail = "  _Tidak ada trade hari ini_"
        best_trade = ""
        worst_trade = ""
    else:
        detail = ""
        for t in trades:
            pair, profit_abs, profit_ratio, close_rate, open_rate, is_short, close_date, tag = t
            arah = "SHORT" if is_short else "LONG"
            hasil = "✅" if profit_abs > 0 else "❌"
            pct = profit_ratio * 100 / 10
            detail += f"  {hasil} `{pair}` {arah} -> `{pct:+.2f}%`\n"
        sorted_trades = sorted(trades, key=lambda x: x[1], reverse=True)
        best = sorted_trades[0]
        worst = sorted_trades[-1]
        best_pct = best[2] * 100 / 10
        worst_pct = worst[2] * 100 / 10
        best_trade = f"  🏆 Best: `{best[0]}` -> `{best_pct:+.2f}%`\n"
        worst_trade = f"  💀 Worst: `{worst[0]}` -> `{worst_pct:+.2f}%`\n"

    overall_stats = ""
    if profit_stats:
        total_trades_all = profit_stats.get('trade_count', 0)
        win_all = profit_stats.get('winning_trades', 0)
        loss_all = profit_stats.get('losing_trades', 0)
        winrate_all = (win_all / total_trades_all * 100) if total_trades_all > 0 else 0
        profit_factor = profit_stats.get('profit_factor', 0)
        avg_duration = profit_stats.get('avg_duration', 'N/A')
        best_pair = profit_stats.get('best_pair', 'N/A')
        if isinstance(best_pair, dict):
            best_pair = best_pair.get('key', 'N/A')
        max_drawdown = profit_stats.get('max_drawdown_abs', 0)
        roi_closed = profit_stats.get('profit_closed_ratio_sum', 0) * 100 / 10

        overall_stats = (
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📊 *Statistik Keseluruhan:*\n"
            f"  • Total Trade: `{total_trades_all}`\n"
            f"  • Win/Loss: `{win_all}/{loss_all}`\n"
            f"  • Winrate: `{winrate_all:.1f}%`\n"
            f"  • Profit Factor: `{profit_factor:.2f}`\n"
            f"  • Avg Duration: `{avg_duration}`\n"
            f"  • Best Pair: `{best_pair}`\n"
            f"  • Max Drawdown: `{max_drawdown:.4f} USDT`\n"
            f"  • ROI Total: `{roi_closed:+.2f}%`\n"
        )

    pesan = (
        f"📊 *DAILY REPORT — JARVIS x BADUT KOTA*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📅 *Tanggal:* `{today}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📈 *Performa Hari Ini:*\n"
        f"  • Total Trade: `{total}`\n"
        f"  • Win: `{wins}` ✅\n"
        f"  • Loss: `{losses}` ❌\n"
        f"  • Winrate: `{winrate:.1f}%`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Total PnL Hari Ini:* {pnl_emoji} `{pnl_sign}{total_pnl:.4f} USDT`\n"
        f"💼 *Saldo Sekarang:* {balance_str}\n"
        f"{drawdown_line}"
        f"{best_trade}"
        f"{worst_trade}"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📋 *Detail Trade Hari Ini:*\n"
        f"{detail}"
        f"{overall_stats}"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🤖 *Jarvis* — _AI Trading Bot_\n"
        f"🎪 *Badut Kota* — _@badutkota147_\n"
        f"📦 *Repo:* github.com/sahar147/jarvis\_ventures"
    )

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    resp = requests.post(url, json={"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"}, timeout=10)
    data = resp.json()
    if resp.status_code == 200:
        print("[Report] Terkirim!")
        msg_id = data["result"]["message_id"]
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/pinChatMessage",
            json={"chat_id": CHAT_ID, "message_id": msg_id, "disable_notification": False},
            timeout=10
        )
        print("[Report] Di-pin!")
    else:
        print(f"[Report] Gagal: {data}")

if __name__ == "__main__":
    send_daily_report()
