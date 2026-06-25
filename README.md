# 🤖 Jarvis Ventures — Auto Trading Bot

Bot trading Freqtrade otomatis untuk Binance Futures.
Strategi: TrendPullbackStrategy

## Channel Telegram
@badut_kota

## Filter Entry
1. EMA50 > EMA200 H1 → konfirmasi trend
2. Pullback ke EMA21 → entry di support/resistance
3. EMA gap > close x 0.002 → anti chop
4. ADX > 23 → trend kuat
5. Volume > MA5 → ada momentum

## Risk Management
- SL: -3% harga = -30% modal
- TP: +6% harga = +60% modal
- RR: 1:2
- Leverage: 10x Isolated

## Panduan Pemasangan
Lihat INSTALL.md

## Struktur File
- TrendPullbackStrategy.py → strategi utama
- daily_report.py → laporan harian
- weekly_report.py → laporan mingguan
- monthly_report.py → laporan bulanan
- balance_alert.py → alert saldo minimum
- INSTALL.md → panduan pemasangan lengkap

Jarvis Ventures — AI Trading Bot x Badut Kota 🤖🎪
