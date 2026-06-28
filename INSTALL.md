# JARVIS VENTURES — PANDUAN INSTALASI

Repo: github.com/sahar147/jarvis_ventures
Channel: t.me/badut_kota (@badutkota147)

---

## REQUIREMENTS
- VPS Ubuntu 20.04/22.04
- Docker + Docker Compose
- Akun Binance dengan Futures aktif
- Bot Telegram (dari @BotFather)
- Channel Telegram

---

## LANGKAH 1 — INSTALL DOCKER
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
sudo apt install docker-compose-plugin -y

## LANGKAH 2 — CLONE REPO
git clone https://github.com/sahar147/jarvis_ventures.git
cd jarvis_ventures
mkdir -p user_data/strategies

## LANGKAH 3 — SETUP FILE
cp SniperStrategy.py user_data/strategies/
cp jarvis_settings.json user_data/

## LANGKAH 4 — EDIT CONFIG
nano config.json
Ganti:
- YOUR_BINANCE_API_KEY
- YOUR_BINANCE_API_SECRET
- YOUR_BOT_TOKEN (telegram pribadi)
- YOUR_CHAT_ID (telegram pribadi)
- YOUR_SIGNAL_BOT_TOKEN (bot signal)
- YOUR_SIGNAL_CHAT_ID (channel signal)

## LANGKAH 5 — EDIT STRATEGI
nano user_data/strategies/SniperStrategy.py
Ganti:
- YOUR_BOT_TOKEN
- YOUR_CHAT_ID

## LANGKAH 6 — EDIT JARVIS SETTINGS
nano user_data/jarvis_settings.json
Ganti "Nama Kamu" dengan nama kamu
time_filter: true = aktif 03-21 UTC
time_filter: false = 24 jam non-stop

## LANGKAH 7 — JALANKAN BOT
docker compose up -d

## LANGKAH 8 — CEK BOT
docker compose logs freqtrade --tail 20
Kalau ada "RUNNING" berarti bot aktif!

---

## STRATEGI: SniperStrategy
- Timeframe: 5m + trend 1H
- Entry: BB breakout + RSI + EMA21 + ATR + Volume
- Leverage: 15x Cross Margin
- SL: -1% harga = -15% margin
- TP: +2% harga = +30% margin
- RR: 1:2
- Stake: 33.3% saldo → loss ~5% per SL
- Max trade: 1
- Stoploss on exchange: aktif

---

## OPERASIONAL
docker compose logs freqtrade --tail 20   # cek log
docker compose restart freqtrade           # restart
docker compose down                        # stop

---

## PENTING
- Gunakan modal yang sanggup kamu tanggung ruginya
- Jangan gunakan uang pinjaman
- Bot tidak menjamin profit
- Selalu monitor performa bot

---

## IKUTI CHANNEL SIGNAL
t.me/badut_kota (@badutkota147)
