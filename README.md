# 🤖 Jarvis Ventures — Auto Trading Bot

Bot trading Freqtrade otomatis untuk Binance Futures.
Strategi: TrendPullbackStrategy

## Channel Telegram
@badut_kota → https://t.me/badut_kota

## Filter Entry
1. EMA50 > EMA200 H1 → konfirmasi trend
2. Pullback ke EMA21 → entry di support/resistance
3. EMA gap > close x 0.002 → anti chop
4. ADX > 23 → trend kuat
5. Volume > MA5 → ada momentum
6. Market Regime BTC EMA200 1D → ikut tren besar

## Risk Management
- SL: -2% harga = -20% modal
- TP: +4% harga = +40% modal
- RR: 1:2
- Leverage: 20x Isolated
- Ratio: 0.125

## Panduan Pemasangan
Lihat INSTALL.md

## Update Strategi Terbaru
    cd ~/freqtrade/user_data/strategies
    curl -O https://raw.githubusercontent.com/sahar147/jarvis_ventures/main/TrendPullbackStrategy.py
    cd ~/freqtrade && docker compose restart freqtrade

## Struktur File
- TrendPullbackStrategy.py → strategi utama
- config.json → contoh konfigurasi
- daily_report.py → laporan harian
- weekly_report.py → laporan mingguan
- monthly_report.py → laporan bulanan
- balance_alert.py → alert saldo minimum
- jarvis_settings.json → settings tanpa restart
- INSTALL.md → panduan pemasangan lengkap

Jarvis Ventures — AI Trading Bot x Badut Kota 🤖🎪
