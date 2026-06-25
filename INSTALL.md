# Panduan Pemasangan Jarvis Ventures

Repo: https://github.com/sahar147/jarvisventures_channel
Update: 25 Juni 2026

---

## LANGKAH 1 - PERSIAPAN SERVER

VPS Ubuntu minimal 2GB RAM

    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    sudo apt install docker-compose-plugin

---

## LANGKAH 2 - SETUP FREQTRADE

    mkdir ~/freqtrade && cd ~/freqtrade
    curl https://raw.githubusercontent.com/freqtrade/freqtrade/stable/docker-compose.yml -o docker-compose.yml
    mkdir -p user_data/strategies user_data/data

---

## LANGKAH 3 - CLONE REPO JARVIS

    git clone https://github.com/sahar147/jarvisventures_channel.git /tmp/jarvis
    cp /tmp/jarvis/user_data/strategies/TrendPullbackStrategy.py ~/freqtrade/user_data/strategies/
    cp /tmp/jarvis/user_data/daily_report.py ~/freqtrade/user_data/
    cp /tmp/jarvis/user_data/weekly_report.py ~/freqtrade/user_data/
    cp /tmp/jarvis/user_data/monthly_report.py ~/freqtrade/user_data/
    cp /tmp/jarvis/user_data/balance_alert.py ~/freqtrade/user_data/

---

## LANGKAH 4 - BUAT CONFIG.JSON

    {
        "max_open_trades": 1,
        "stake_currency": "USDT",
        "stake_amount": "unlimited",
        "tradable_balance_ratio": 0.33,
        "fiat_display_currency": "USD",
        "dry_run": true,
        "cancel_open_orders_on_exit": false,
        "trading_mode": "futures",
        "margin_mode": "isolated",
        "exchange": {
            "name": "binance",
            "key": "API_KEY_BINANCE",
            "secret": "API_SECRET_BINANCE",
            "ccxt_config": {"defaultType": "swap"},
            "pair_blacklist": [
                "BNB/.*",
                "HYPE/USDT:USDT",
                "AVAX/USDT:USDT",
                "AMZN/USDT:USDT",
                "META/USDT:USDT",
                "NVDA/USDT:USDT",
                "GOOGL/USDT:USDT",
                "AAPL/USDT:USDT",
                "MSFT/USDT:USDT",
                "TSLA/USDT:USDT",
                "JPM/USDT:USDT",
                "V/USDT:USDT",
                "BRKB/USDT:USDT"
            ]
        },
        "pairlists": [
            {
                "method": "VolumePairList",
                "number_assets": 20,
                "sort_key": "quoteVolume",
                "min_value": 5000000,
                "refresh_period": 1800
            },
            {"method": "AgeFilter", "min_days_listed": 30},
            {
                "method": "RangeStabilityFilter",
                "lookback_period_candles": 3,
                "min_rate_of_change": 0.02
            }
        ],
        "telegram": {
            "enabled": true,
            "token": "TOKEN_BOT_FREQTRADE_PRIBADI",
            "chat_id": "CHAT_ID_PRIBADI",
            "notification_settings": {"status": "off"}
        },
        "api_server": {
            "enabled": true,
            "listen_ip_address": "0.0.0.0",
            "listen_port": 8080,
            "verbosity": "error",
            "enable_openapi": false,
            "jwt_secret_key": "RANDOM_STRING_PANJANG",
            "username": "USERNAME_BEBAS",
            "password": "PASSWORD_KUAT"
        },
        "bot_name": "jarvis",
        "strategy": "TrendPullbackStrategy",
        "telegram_signal": {
            "token": "TOKEN_BOT_SIGNAL_CHANNEL",
            "chat_id": "CHAT_ID_CHANNEL"
        }
    }

---

## LANGKAH 5 - BUAT JARVIS SETTINGS

    python3 -c "
    import json
    s = {'time_filter': False, 'smart_exit': False}
    with open('/root/freqtrade/user_data/jarvis_settings.json', 'w') as f:
        json.dump(s, f, indent=4)
    print('Done!')
    "

time_filter false = 24 jam non-stop
time_filter true = aktif jam 03-21 UTC
smart_exit false = murni TP/SL
smart_exit true = bersih posisi profit jam 21 UTC

---

## LANGKAH 6 - SETUP TELEGRAM

Bot Freqtrade (notif pribadi):
1. Chat @BotFather - /newbot - dapat token
2. Masuk ke config telegram.token
3. Chat bot - dapat chat_id - masuk telegram.chat_id

Bot Signal Channel:
1. Buat bot baru via @BotFather
2. Token masuk telegram_signal.token
3. Buat channel Telegram
4. Tambah bot sebagai Admin channel
5. Kirim pesan di channel
6. Akses https://api.telegram.org/botTOKEN/getUpdates
7. Cari chat id format -100xxxxxxxxxx
8. Masuk ke telegram_signal.chat_id

---

## LANGKAH 7 - API KEY BINANCE

1. Binance - API Management - buat API key baru
2. Permission: Enable Futures (Read + Trade)
3. JANGAN aktifkan withdrawal
4. Whitelist IP server VPS
5. Masukkan ke config.json

---

## LANGKAH 8 - DRY RUN TEST

    cd ~/freqtrade && docker compose up -d
    docker compose logs freqtrade --tail 20

Test minimal 3 hari sebelum live!

---

## LANGKAH 9 - GO LIVE

    python3 -c "
    import json
    with open('/root/freqtrade/user_data/config.json', 'r') as f:
        config = json.load(f)
    config['dry_run'] = False
    with open('/root/freqtrade/user_data/config.json', 'w') as f:
        json.dump(config, f, indent=4)
    print('Live mode aktif!')
    "
    cd ~/freqtrade && docker compose restart freqtrade

---

## LANGKAH 10 - SETUP CRON JOBS

    (crontab -l 2>/dev/null; echo "0 0 * * * docker compose -f /root/freqtrade/docker-compose.yml exec -T freqtrade python3 /freqtrade/user_data/daily_report.py >> /root/freqtrade/user_data/daily_report.log 2>&1") | crontab -
    (crontab -l 2>/dev/null; echo "0 0 * * 1 docker compose -f /root/freqtrade/docker-compose.yml exec -T freqtrade python3 /freqtrade/user_data/weekly_report.py weekly >> /root/freqtrade/user_data/weekly_report.log 2>&1") | crontab -
    (crontab -l 2>/dev/null; echo "0 0 1 * * docker compose -f /root/freqtrade/docker-compose.yml exec -T freqtrade python3 /freqtrade/user_data/monthly_report.py monthly >> /root/freqtrade/user_data/monthly_report.log 2>&1") | crontab -
    (crontab -l 2>/dev/null; echo "30 * * * * docker compose -f /root/freqtrade/docker-compose.yml exec -T freqtrade python3 /freqtrade/user_data/monthly_report.py winrate >> /root/freqtrade/user_data/winrate.log 2>&1") | crontab -
    (crontab -l 2>/dev/null; echo "0 * * * * docker compose -f /root/freqtrade/docker-compose.yml exec -T freqtrade python3 /freqtrade/user_data/balance_alert.py >> /root/freqtrade/user_data/balance_alert.log 2>&1") | crontab -

---

## STRATEGI: TrendPullbackStrategy

Filter Entry:
1. EMA50 > EMA200 H1 → konfirmasi trend H1
2. Pullback ke EMA21 → entry di support/resistance
3. EMA gap > close x 0.002 → anti chop/sideways
4. ADX > 23 → trend harus kuat
5. Volume > MA5 → ada momentum

EMA yang dipakai:
- EMA21, EMA50, EMA200 di 5m
- EMA21, EMA50, EMA200 di 1h
- EMA21, EMA50, EMA200 di 4h

Risk Management:
- SL: -3% harga = -30% modal
- TP: +6% harga = +60% modal
- RR: 1:2
- Leverage: 10x Isolated

---

## CARA UBAH SETTINGS TANPA RESTART

ON/OFF time filter:
    python3 -c "import json; f=open('/root/freqtrade/user_data/jarvis_settings.json','r+'); s=json.load(f); s['time_filter']=True; f.seek(0); json.dump(s,f,indent=4); print('ON!')"

ON/OFF smart exit:
    python3 -c "import json; f=open('/root/freqtrade/user_data/jarvis_settings.json','r+'); s=json.load(f); s['smart_exit']=True; f.seek(0); json.dump(s,f,indent=4); print('ON!')"

---

## OPERASIONAL

Restart: cd ~/freqtrade && docker compose restart freqtrade
Log: docker compose logs freqtrade --tail 20
Cron: crontab -l
Push: git push origin main && git push channel main

Update file tanpa nano:
    python3 -c "
    with open('/path/file', 'r') as f:
        content = f.read()
    content = content.replace('old', 'new')
    with open('/path/file', 'w') as f:
        f.write(content)
    print('Done!')
    "

---

## TROUBLESHOOTING

- Warning minimum stake = kurangi max_open_trades
- Error strategy = cek sintaks Python
- Bot tidak entry = cek filter terlalu ketat atau pair tidak lolos
- Telegram tidak kirim = cek token dan chat_id
- Bot crash = docker compose logs freqtrade --tail 50

---

## UPDATE STRATEGI TERBARU

Kalau ada update dari repo, jalankan:

    cd ~/freqtrade/user_data/strategies
    curl -O https://raw.githubusercontent.com/sahar147/jarvis_ventures/main/TrendPullbackStrategy.py
    cd ~/freqtrade && docker compose restart freqtrade

Atau kalau clone full repo:

    cd ~/jarvis_ventures
    git pull origin main
    cp TrendPullbackStrategy.py ~/freqtrade/user_data/strategies/
    cd ~/freqtrade && docker compose restart freqtrade

---

Jarvis Ventures - AI Trading Bot x Badut Kota
