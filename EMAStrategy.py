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
        balance = signal.get("balance", 0)
        stake = balance * 0.667 if balance < 50 else balance * 0.333
        saldo_sl = balance - (stake * 0.15)
        saldo_tp = balance + (stake * 0.30)
        pesan = (
            f"⚡ *ENTRY — JARVIS EMA*\n"
            f"📌 *{signal['pair']}* {arah}\n"
            f"💰 Entry: `{signal['entry_price']:.4f} USDT`\n"
            f"🛡 SL: `{sl_price:.4f} USDT` ({sl_pct})\n"
            f"🎯 TP: `{tp_price:.4f} USDT` ({tp_pct})\n"
            f"📊 RSI: `{signal['rsi']:.1f}` | Vol: ✅ | ATR: ✅\n"
            f"🌍 Regime: {regime_text}\n"
            f"💼 Saldo: `{balance:.2f}` | SL→`{saldo_sl:.2f}` | TP→`{saldo_tp:.2f}` USDT\n"
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

def send_telegram_cancel(token: str, chat_id: str, cancel_info: dict):
    try:
        pair = cancel_info["pair"]
        side = cancel_info["side"]
        arah = "LONG" if side == "long" else "SHORT"
        balance = cancel_info.get("balance", 0)
        pesan = (
            f"⚠️ *ORDER CANCELLED — JARVIS*\n"
            f"📌 *{pair}* {arah}\n"
            f"❌ Order dibatalkan (timeout)\n"
            f"💼 Saldo: `{balance:.2f} USDT`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🤖 *Jarvis* x *Badut Kota*\n"
            f"👤 Owner: _Pakdendam_"
        )
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(url, json={"chat_id": chat_id, "text": pesan, "parse_mode": "Markdown"}, timeout=10)
        if resp.status_code != 200:
            print(f"[Telegram Cancel] Gagal: {resp.text}")
        else:
            print(f"[Telegram Cancel] Notif terkirim: {pair}")
    except Exception as e:
        print(f"[Telegram Cancel] Error: {e}")

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
        elif reason in ("stop_loss", "trailing_stop_loss", "stoploss_on_exchange"):
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

class EMAStrategy(IStrategy):
    INTERFACE_VERSION = 3
    can_short: bool = True
    timeframe = "5m"
    minimal_roi = {"0": 0.30}
    stoploss = -0.15
    trailing_stop = False
    process_only_new_candles = True
    use_exit_signal = True
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


    @informative("1h")
    def populate_indicators_1h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema7"] = ta.EMA(dataframe, timeperiod=7)
        dataframe["ema25"] = ta.EMA(dataframe, timeperiod=25)
        dataframe["ema99"] = ta.EMA(dataframe, timeperiod=99)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 3 EMA
        dataframe["ema7"] = ta.EMA(dataframe, timeperiod=7)
        dataframe["ema25"] = ta.EMA(dataframe, timeperiod=25)
        dataframe["ema99"] = ta.EMA(dataframe, timeperiod=99)

        # ATR
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=3)
        dataframe["atr_median"] = dataframe["atr"].rolling(6).median()

        # Volume
        dataframe["volume_ma20"] = dataframe["volume"].rolling(3).mean()

        # RSI
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)

        # Golden cross: EMA8 cross atas EMA21
        dataframe["golden_cross"] = (
            (dataframe["ema7"] > dataframe["ema25"]) &
            (dataframe["ema7"].shift(1) <= dataframe["ema25"].shift(1))
        )

        # Death cross: EMA8 cross bawah EMA21
        dataframe["death_cross"] = (
            (dataframe["ema7"] < dataframe["ema25"]) &
            (dataframe["ema7"].shift(1) >= dataframe["ema25"].shift(1))
        )

        # METODE 1: Cross baru (max 3 candle) + semua indikator
        recent_golden = (
            dataframe["golden_cross"] |
            dataframe["golden_cross"].shift(1) |
            dataframe["golden_cross"].shift(2)
        )
        entry_long_m1 = (
            recent_golden &
            (dataframe["ema7"] > dataframe["ema25"]) &
            (dataframe["ema25"] > dataframe["ema99"]) &
            (dataframe["close"] > dataframe["ema7"]) &
            (dataframe["volume"] > dataframe["volume_ma20"] * 1.5) &
            (dataframe["rsi"] >= 45) &
            (dataframe["rsi"] <= 70) &
            (dataframe["atr"] > dataframe["atr_median"])
        )
        # METODE 2: Alignment + retest bounce EMA7 (tanpa batas candle)
        pullback_long = dataframe["low"] <= dataframe["ema7"]
        bounce_long = dataframe["close"] > dataframe["ema7"]
        entry_long_m2 = (
            (dataframe["ema7"] > dataframe["ema25"]) &
            (dataframe["ema25"] > dataframe["ema99"]) &
            pullback_long &
            bounce_long &
            (dataframe["volume"] > dataframe["volume_ma20"] * 1.5) &
            (dataframe["rsi"] >= 45) &
            (dataframe["rsi"] <= 70) &
            (dataframe["atr"] > dataframe["atr_median"])
        )
        dataframe["entry_long"] = (entry_long_m1 | entry_long_m2) & (dataframe["ema7_1h"] > dataframe["ema25_1h"]) & (dataframe["ema25_1h"] > dataframe["ema99_1h"])

        # METODE 1: Cross baru (max 3 candle) + semua indikator
        recent_death = (
            dataframe["death_cross"] |
            dataframe["death_cross"].shift(1) |
            dataframe["death_cross"].shift(2)
        )
        entry_short_m1 = (
            recent_death &
            (dataframe["ema7"] < dataframe["ema25"]) &
            (dataframe["ema25"] < dataframe["ema99"]) &
            (dataframe["close"] < dataframe["ema7"]) &
            (dataframe["volume"] > dataframe["volume_ma20"] * 1.5) &
            (dataframe["rsi"] >= 30) &
            (dataframe["rsi"] <= 55) &
            (dataframe["atr"] > dataframe["atr_median"])
        )
        # METODE 2: Alignment + retest bounce EMA7 (tanpa batas candle)
        pullback_short = dataframe["high"] >= dataframe["ema7"]
        bounce_short = dataframe["close"] < dataframe["ema7"]
        entry_short_m2 = (
            (dataframe["ema7"] < dataframe["ema25"]) &
            (dataframe["ema25"] < dataframe["ema99"]) &
            pullback_short &
            bounce_short &
            (dataframe["volume"] > dataframe["volume_ma20"] * 1.5) &
            (dataframe["rsi"] >= 30) &
            (dataframe["rsi"] <= 55) &
            (dataframe["atr"] > dataframe["atr_median"])
        )
        dataframe["entry_short"] = (entry_short_m1 | entry_short_m2) & (dataframe["ema7_1h"] < dataframe["ema25_1h"]) & (dataframe["ema25_1h"] < dataframe["ema99_1h"])

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["entry_long"])
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "ema_golden_cross")
        dataframe.loc[
            (
                (dataframe["entry_short"])
            ),
            ["enter_short", "enter_tag"],
        ] = (1, "ema_death_cross")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, "exit_long"] = 0
        dataframe.loc[:, "exit_short"] = 0
        return dataframe

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float,
                            rate: float, time_in_force: str, entry_tag: str,
                            side: str, **kwargs) -> bool:
        try:
            import json as _json
            with open("/freqtrade/user_data/jarvis_settings.json") as f:
                settings = _json.load(f)
        except:
            settings = {"time_filter": False}
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
                "balance": float(self.wallets.get_total_balance("USDT")),
            }
            if self.tg_token and self.tg_chat_id:
                send_telegram_signal(self.tg_token, self.tg_chat_id, signal)
                print(f"[Telegram Entry] Notif terkirim: {pair}")
        except Exception as e:
            print(f"[Telegram Entry] Error: {e}")
        return True

    def check_entry_timeout(self, pair: str, trade, order: dict,
                            current_time, **kwargs) -> bool:
        try:
            if self.tg_token and self.tg_chat_id:
                cancel_info = {
                    "pair": pair,
                    "side": "short" if trade.is_short else "long",
                    "balance": float(self.wallets.get_total_balance("USDT")),
                }
                send_telegram_cancel(self.tg_token, self.tg_chat_id, cancel_info)
        except Exception as e:
            print(f"[Cancel] Error: {e}")
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
