# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
from freqtrade.strategy import IStrategy, informative
from pandas import DataFrame
import talib.abstract as ta
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timezone

def send_telegram(token: str, chat_id: str, pesan: str):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(url, json={"chat_id": chat_id, "text": pesan, "parse_mode": "Markdown"}, timeout=10)
        if resp.status_code != 200:
            print(f"[Telegram] Gagal: {resp.text}")
    except Exception as e:
        print(f"[Telegram] Error: {e}")

def send_telegram_signal(token: str, chat_id: str, signal: dict):
    try:
        if signal["side"] == "long":
            arah = "LONG"
            sl_price = signal["entry_price"] * 0.99
            tp_price = signal["entry_price"] * 1.02
            sl_pct = "-1%"
            tp_pct = "+2%"
        else:
            arah = "SHORT"
            sl_price = signal["entry_price"] * 1.01
            tp_price = signal["entry_price"] * 0.98
            sl_pct = "+1%"
            tp_pct = "-2%"
        regime_text = "🟢 BULL" if signal["side"] == "long" else "🔴 BEAR"
        pesan = (
            f"⚡ *ENTRY — JARVIS SNIPER*\n"
            f"📌 *{signal['pair']}* {arah}\n"
            f"💰 Entry: `{signal['entry_price']:.4f} USDT`\n"
            f"🛡 SL: `{sl_price:.4f} USDT` ({sl_pct})\n"
            f"🎯 TP: `{tp_price:.4f} USDT` ({tp_pct})\n"
            f"📊 RSI: `{signal['rsi']:.1f}` | Vol: ✅ | ATR: ✅\n"
            f"🌍 Regime: {regime_text}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🤖 *Jarvis* x *Badut Kota*\n"
            f"👤 Owner: _Pakdendam_"
        )
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(url, json={"chat_id": chat_id, "text": pesan, "parse_mode": "Markdown"}, timeout=10)
        if resp.status_code != 200:
            print(f"[Telegram] Gagal kirim: {resp.text}")
        else:
            print(f"[Telegram] Entry terkirim: {signal['pair']} {arah}")
    except Exception as e:
        print(f"[Telegram] Error: {e}")

def send_telegram_exit(token: str, chat_id: str, exit_info: dict):
    try:
        reason = exit_info["reason"]
        profit_pct = exit_info["profit_pct"]
        pair = exit_info["pair"]
        close_rate = exit_info["close_rate"]
        open_rate = exit_info["open_rate"]
        side = exit_info["side"]
        arah = "LONG" if side == "long" else "SHORT"
        profit_sign = "+" if profit_pct >= 0 else ""
        profit_display = profit_pct / 15
        if reason == "roi":
            judul = "🎯 *TP HIT*"
            hasil_emoji = "✅"
        elif reason in ("stop_loss", "trailing_stop_loss"):
            judul = "🛑 *SL HIT*"
            hasil_emoji = "❌"
        else:
            judul = "🔚 *CLOSED*"
            hasil_emoji = "🔄"
        pesan = (
            f"{judul}\n"
            f"📌 *{pair}* {arah}\n"
            f"💰 `{open_rate:.4f}` → `{close_rate:.4f} USDT`\n"
            f"{hasil_emoji} `{profit_sign}{profit_display:.2f}%` harga | `{profit_sign}{profit_pct:.2f}%` margin\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🤖 *Jarvis* x *Badut Kota*\n"
            f"👤 Owner: _Pakdendam_"
        )
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(url, json={"chat_id": chat_id, "text": pesan, "parse_mode": "Markdown"}, timeout=10)
        if resp.status_code != 200:
            print(f"[Telegram Exit] Gagal kirim: {resp.text}")
        else:
            print(f"[Telegram Exit] Notif terkirim: {pair} {reason}")
    except Exception as e:
        print(f"[Telegram Exit] Error: {e}")

class SniperStrategy(IStrategy):
    INTERFACE_VERSION = 3
    can_short: bool = True
    timeframe = "5m"
    minimal_roi = {"0": 0.30}
    stoploss = -0.15
    trailing_stop = False
    trailing_stop_positive = 0.0
    trailing_stop_positive_offset = 0.0
    trailing_only_offset_is_reached = False
    process_only_new_candles = True
    use_exit_signal = False
    startup_candle_count: int = 200
    trade_time_start = 3
    trade_time_end = 21
    _last_session_notice = None
    protections = [
        {"method": "CooldownPeriod", "stop_duration_candles": 5},
        {"method": "StoplossGuard", "lookback_period_candles": 24, "trade_limit": 2, "stop_duration_candles": 4, "only_per_pair": True}
    ]

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        tg = config.get("telegram_signal", {})
        self.tg_token = tg.get("token", "")
        self.tg_chat_id = tg.get("chat_id", "")
        try:
            import json as _json
            with open("/freqtrade/user_data/jarvis_settings.json") as f:
                self._jarvis_settings = _json.load(f)
        except:
            self._jarvis_settings = {"time_filter": False}
        self._last_session_notice = None

    def leverage(self, pair: str, current_time, current_rate: float,
                 proposed_leverage: float, max_leverage: float,
                 entry_tag, side: str, **kwargs) -> float:
        if max_leverage < 15:
            print(f"[LevFilter] Skip {pair} — max leverage {max_leverage}x < 15x")
            return 1.0
        return 15.0

    def is_trading_time(self) -> bool:
        hour = datetime.now(timezone.utc).hour
        return self.trade_time_start <= hour < self.trade_time_end

    def check_session_notice(self):
        try:
            hour = datetime.now(timezone.utc).hour
            wib_hour = (hour + 7) % 24
            session = "active" if self.trade_time_start <= hour < self.trade_time_end else "skip"
            if self._last_session_notice == session:
                return
            self._last_session_notice = session
            waktu_utc = datetime.now(timezone.utc).strftime("%H:%M UTC")
            waktu_wib = f"{wib_hour:02d}:{datetime.now(timezone.utc).strftime('%M')} WIB"
            if session == "active":
                pesan = (
                    f"🟢 *SESI TRADING AKTIF — JARVIS*\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"⏰ *Waktu:* `{waktu_utc}` | `{waktu_wib}`\n"
                    f"📊 *Status:* Bot aktif mencari sinyal\n"
                    f"🕐 *Sesi aktif:* `10.00 - 04.00 WIB`\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🤖 *Jarvis* — _AI Trading Bot_\n"
                    f"🎪 *Badut Kota* — _@badutkota147_"
                )
            else:
                pesan = (
                    f"🔴 *SESI SKIP ENTRY — JARVIS*\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"⏰ *Waktu:* `{waktu_utc}` | `{waktu_wib}`\n"
                    f"📊 *Status:* Bot standby, sesi asia sepi mendingan tidur dulu sayangi modal\n"
                    f"🕐 *Sesi skip:* `04.00 - 10.00 WIB`\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🤖 *Jarvis* — _AI Trading Bot_\n"
                    f"🎪 *Badut Kota* — _@badutkota147_"
                )
            if self.tg_token and self.tg_chat_id:
                send_telegram(self.tg_token, self.tg_chat_id, pesan)
        except Exception as e:
            print(f"[Session Notice] Error: {e}")

    @informative("1h")
    def populate_indicators_1h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # EMA21 dynamic S/R
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)

        # ATR volatility
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_median"] = dataframe["atr"].rolling(50).median()

        # Volume
        dataframe["volume_ma20"] = dataframe["volume"].rolling(20).mean()

        # RSI momentum
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)

        # Bollinger Bands squeeze breakout
        upper, middle, lower = ta.BBANDS(dataframe["close"], timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
        dataframe["bb_upper"] = upper
        dataframe["bb_lower"] = lower
        dataframe["bb_middle"] = middle

        # LONG entry
        dataframe["entry_long"] = (
            (dataframe["close"] > dataframe["ema21"]) &
            (dataframe["close"] > dataframe["bb_upper"].shift(1)) &
            (dataframe["volume"] > dataframe["volume_ma20"] * 1.5) &
            (dataframe["rsi"] >= 45) &
            (dataframe["rsi"] <= 70) &
            (dataframe["atr"] > dataframe["atr_median"])
        )

        # SHORT entry
        dataframe["entry_short"] = (
            (dataframe["close"] < dataframe["ema21"]) &
            (dataframe["close"] < dataframe["bb_lower"].shift(1)) &
            (dataframe["volume"] > dataframe["volume_ma20"] * 1.5) &
            (dataframe["rsi"] >= 30) &
            (dataframe["rsi"] <= 55) &
            (dataframe["atr"] > dataframe["atr_median"])
        )

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["entry_long"]) &
                (dataframe["ema50_1h"] > dataframe["ema200_1h"])
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "sniper_long")
        dataframe.loc[
            (
                (dataframe["entry_short"]) &
                (dataframe["ema50_1h"] < dataframe["ema200_1h"])
            ),
            ["enter_short", "enter_tag"],
        ] = (1, "sniper_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, "exit_long"] = 0
        dataframe.loc[:, "exit_short"] = 0
        return dataframe

    def custom_stake_amount(self, current_time, current_rate, current_profit,
                            proposed_stake, min_stake, max_stake, leverage,
                            entry_tag, side, **kwargs) -> float:
        try:
            balance = self.wallets.get_total_stake_amount()
            stake = balance * 0.333
            return max(min_stake, min(stake, max_stake))
        except Exception as e:
            print(f"[StakeAmount] Error: {e}")
            return proposed_stake

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float,
                            rate: float, time_in_force: str, entry_tag: str,
                            side: str, **kwargs) -> bool:
        try:
            import json as _json
            with open("/freqtrade/user_data/jarvis_settings.json") as f:
                settings = _json.load(f)
        except:
            settings = {"time_filter": False, "owner_name": "Pakdendam"}
        if settings.get("time_filter", False) and not self.is_trading_time():
            print(f"[TimeFilter] Skip entry {pair}")
            return False
        try:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            last = dataframe.iloc[-1]
            signal = {
                "pair": pair,
                "side": side,
                "entry_price": rate,
                "rsi": float(last.get("rsi", 0)),
            }
            if self.tg_token and self.tg_chat_id:
                send_telegram_signal(self.tg_token, self.tg_chat_id, signal)
                print(f"[Telegram Entry] Notif terkirim: {pair}")
        except Exception as e:
            print(f"[Telegram Entry] Error: {e}")
        return True

    def custom_exit(self, pair: str, trade, current_time, current_rate: float,
                    current_profit: float, **kwargs):
        return None

    def confirm_trade_exit(self, pair: str, trade, order_type: str, amount: float,
                           rate: float, time_in_force: str, exit_reason: str,
                           **kwargs) -> bool:
        try:
            if self.tg_token and self.tg_chat_id:
                side = "short" if trade.is_short else "long"
                if trade.is_short:
                    profit_pct = (trade.open_rate - rate) / trade.open_rate * 100
                else:
                    profit_pct = (rate - trade.open_rate) / trade.open_rate * 100
                exit_info = {
                    "pair": pair,
                    "side": side,
                    "open_rate": trade.open_rate,
                    "close_rate": rate,
                    "profit_pct": profit_pct * 15,
                    "reason": exit_reason,
                }
                send_telegram_exit(self.tg_token, self.tg_chat_id, exit_info)
        except Exception as e:
            print(f"[Telegram Exit] Error: {e}")
        return True
