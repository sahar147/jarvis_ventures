# Panduan Pemasangan Jarvis Ventures

> Sebelum menggunakan, **WAJIB** ikuti channel Telegram kami!
> 👉 [t.me/badut_kota](https://t.me/badut_kota)

## LANGKAH 1 - SERVER
VPS Ubuntu minimal 2GB RAM
curl -fsSL https://get.docker.com | sh
sudo apt install docker-compose-plugin -y

## LANGKAH 2 - CLONE
git clone https://github.com/sahar147/jarvis_ventures.git ~/freqtrade

## LANGKAH 3 - CONFIG
Edit config.json: isi API key Binance, token Telegram bot pribadi dan channel signal

## LANGKAH 4 - JALANKAN
cd ~/freqtrade && docker compose up -d

## STRATEGI: Breakout Momentum
- EMA50 > EMA200 H1
- Close > High/Low 20 candle
- Volume > MA20, ATR > 0.0025, ADX > 20
- SL: -1.5% harga | TP: +3% harga | RR 1:2
- Leverage 10x Cross
- Saldo < $50 = Risk 10% | Saldo >= $50 = Risk 5%

## SETTINGS TANPA RESTART
Edit jarvis_settings.json:
- time_filter: true/false
- owner_name: nama kamu

## Disclaimer
Trading futures berisiko tinggi. Gunakan dengan bijak.

Jarvis - AI Trading Bot | Badut Kota @badutkota147 | Owner: Pakdendam
