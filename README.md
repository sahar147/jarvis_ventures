# 🤖 Jarvis Ventures — Automated Crypto Futures Trading Bot

Bot trading otomatis berbasis **Freqtrade** untuk **Binance Futures** dengan strategi **Breakout Momentum**.

---

## 📡 Ikuti Channel Signal Kami

> ⚠️ **Sebelum menggunakan strategi ini, WAJIB ikuti channel Telegram kami terlebih dahulu untuk memantau performa bot secara real-time sebelum memutuskan untuk menggunakannya!**

### 👉 [t.me/badut_kota](https://t.me/badut_kota)

Channel berisi:
- ⚡ Notif Entry real-time
- 🎯 Notif TP Hit / 🛑 SL Hit
- 📊 Daily, Weekly, Monthly Report
- 🤖 Powered by Jarvis AI Trading Bot

---

## 📌 Strategi: Breakout Momentum

**Timeframe:** 5m (konfirmasi H1)

**Filter Entry:**
- EMA50 > EMA200 di H1 (trend filter)
- Close > High 20 candle lalu (LONG) / Close < Low 20 candle lalu (SHORT)
- Volume > MA20
- ATR > 0.0025
- ADX > 20
- Min leverage pair: 10x

**Risk Management:**
- Leverage: 10x Cross margin
- SL: -1.5% harga
- TP: +3% harga (RR 1:2)
- Saldo < $50 → Risk 10% per trade
- Saldo ≥ $50 → Risk 5% per trade

---

## ⚙️ Setup

1. Install Freqtrade
2. Clone repo ini
3. Isi config.json dengan API key Binance
4. Isi token dan chat_id Telegram
5. Jalankan bot

```bash
docker compose up -d
⚠️ Disclaimer
Trading futures mengandung risiko tinggi. Gunakan dengan bijak. Hasil masa lalu tidak menjamin hasil masa depan.
🤖 Jarvis — AI Trading Bot
🎪 Badut Kota — @badutkota147
👤 **Owner** — *Pakdendam*
