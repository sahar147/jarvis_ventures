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
            sl_price = signal["entry_price"] * 0.98
            tp_price = signal["entry_price"] * 1.04
            sl_pct = "-2%"
            tp_pct = "+4%"
        else:
            arah = "SHORT"
            sl_price = signal["entry_price"] * 1.02
            tp_price = signal["entry_price"] * 0.96
            sl_pct = "+2%"
            tp_pct = "-4%"

        slope_emoji = "▲" if signal["side"] == "long" else "▼"
        regime_text = "🟢 BULL" if signal.get("regime_bull", True) else "🔴 BEAR"

        pesan = (
            f"⚡ *ENTRY — JARVIS*\n"
            f"📌 *{signal['pair']}* {arah}\n"
            f"💰 Entry: `{signal['entry_price']:.4f} USDT`\n"
            f"🛡 SL: `{sl_price:.4f} USDT` ({sl_pct})\n"
            f"🎯 TP: `{tp_price:.4f} USDT` ({tp_pct})\n"
            f"📊 ADX: `{signal['adx']:.1f}` | Slope: {slope_emoji} | Gap: ✅\n"
            f"🌍 Regime: {regime_text}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🤖 *Jarvis* x *Badut Kota*\n"
            f"👤 Owner: _{settings.get("owner_name", "Pakdendam")}_"
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
        profit_display = profit_pct / 10

        if reason == "roi":
            judul = "🎯 *TP HIT*"
            hasil_emoji = "✅"
        elif reason in ("stop_loss", "trailing_stop_loss"):
            judul = "🛑 *SL HIT*"
            hasil_emoji = "❌"
        elif "smart_exit" in reason:
            judul = "⏱ *SMART EXIT 2 JAM*"
            hasil_emoji = "✅" if profit_pct >= 0 else "❌"
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
            f"👤 Owner: _{settings.get("owner_name", "Pakdendam")}_"
        )
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(url, json={"chat_id": chat_id, "text": pesan, "parse_mode": "Markdown"}, timeout=10)
        if resp.status_code != 200:
            print(f"[Telegram Exit] Gagal kirim: {resp.text}")
        else:
            print(f"[Telegram Exit] Notif terkirim: {pair} {reason}")
    except Exception as e:
        print(f"[Telegram Exit] Error: {e}")

class TrendPullbackStrategy(IStrategy):
    INTERFACE_VERSION = 3
    can_short: bool = True
    timeframe = "5m"
    minimal_roi = {"0": 0.80}
    stoploss = -0.40
    trailing_stop = False
    trailing_stop_positive = 0.0
    trailing_stop_positive_offset = 0.0
    trailing_only_offset_is_reached = False
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count: int = 200
    ma_fast = 21
    ma_slow = 50
    ma_trend = 200
    score_threshold = 4

    # Jam trading aktif UTC (03.00 - 21.00 UTC = 10.00 - 04.00 WIB)
    trade_time_start = 3   # 03.00 UTC
    trade_time_end = 21    # 21.00 UTC

    # Simpan status jam untuk notif sekali saja
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
        # Load jarvis settings
        try:
            import json as _json
            with open("/freqtrade/user_data/jarvis_settings.json") as f:
                self._jarvis_settings = _json.load(f)
        except:
            self._jarvis_settings = {"time_filter": False, "smart_exit": False}
        self._last_session_notice = None

    def leverage(self, pair: str, current_time, current_rate: float,
                 proposed_leverage: float, max_leverage: float,
                 entry_tag, side: str, **kwargs) -> float:
        return 20.0

    def is_trading_time(self) -> bool:
        hour = datetime.now(timezone.utc).hour
        return self.trade_time_start <= hour < self.trade_time_end

    def check_session_notice(self):
        """Kirim notif ke channel saat ganti sesi — sekali saja per sesi."""
        try:
            hour = datetime.now(timezone.utc).hour
            wib_hour = (hour + 7) % 24

            if self.trade_time_start <= hour < self.trade_time_end:
                session = "active"
            else:
                session = "skip"

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
                    f"📊 *Status:* Bot standby, hindari jam sepi\n"
                    f"🕐 *Sesi skip:* `04.00 - 10.00 WIB`\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🤖 *Jarvis* — _AI Trading Bot_\n"
                    f"🎪 *Badut Kota* — _@badutkota147_"
                )

            if self.tg_token and self.tg_chat_id:
                send_telegram(self.tg_token, self.tg_chat_id, pesan)
        except Exception as e:
            print(f"[Session Notice] Error: {e}")

    @informative("1d")
    def populate_indicators_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        return dataframe

    @informative("1h")
    def populate_indicators_1h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        return dataframe

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=self.ma_fast)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=self.ma_slow)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=self.ma_trend)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        bull = pd.Series(0, index=dataframe.index)
        bull += (dataframe["close"] > dataframe["ema200"]).astype(int)
        bull += (dataframe["ema21"] > dataframe["ema50"]).astype(int)
        bull += (dataframe["close"] > dataframe["ema200_1h"]).astype(int)
        bull += (dataframe["ema21_1h"] > dataframe["ema50_1h"]).astype(int)
        bull += (dataframe["close"] > dataframe["ema200_4h"]).astype(int)
        bull += (dataframe["ema21_4h"] > dataframe["ema50_4h"]).astype(int)
        dataframe["bull_score"] = bull
        bear = pd.Series(0, index=dataframe.index)
        bear += (dataframe["close"] < dataframe["ema200"]).astype(int)
        bear += (dataframe["ema21"] < dataframe["ema50"]).astype(int)
        bear += (dataframe["close"] < dataframe["ema200_1h"]).astype(int)
        bear += (dataframe["ema21_1h"] < dataframe["ema50_1h"]).astype(int)
        bear += (dataframe["close"] < dataframe["ema200_4h"]).astype(int)
        bear += (dataframe["ema21_4h"] < dataframe["ema50_4h"]).astype(int)
        dataframe["bear_score"] = bear
        # Market Regime Detection pakai EMA200 1D
        if "ema200_1d" in dataframe.columns:
            dataframe["market_bull"] = dataframe["close"] > dataframe["ema200_1d"]
            dataframe["market_bear"] = dataframe["close"] < dataframe["ema200_1d"]
        else:
            dataframe["market_bull"] = True
            dataframe["market_bear"] = True

        # EMA21 slope filter (EMA21 harus miring)



        # EMA21 slope filter
        dataframe["ema21_slope"] = dataframe["ema21"] - dataframe["ema21"].shift(3)

        # Anti chop: EMA21 dan EMA50 harus cukup jauh
        dataframe["ema_gap"] = abs(dataframe["ema21"] - dataframe["ema50"])

        dataframe["pullback_long"] = (
            (dataframe["low"] <= dataframe["ema21"]) &
            (dataframe["close"] > dataframe["ema21"]) &
            (dataframe["close"] > dataframe["open"]) &
            (dataframe["ema_gap"] > dataframe["close"] * 0.002)
        )
        dataframe["pullback_short"] = (
            (dataframe["high"] >= dataframe["ema21"]) &
            (dataframe["close"] < dataframe["ema21"]) &
            (dataframe["close"] < dataframe["open"]) &
            (dataframe["ema_gap"] > dataframe["close"] * 0.002)
        )
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # LONG searah BTC (bull)
        dataframe.loc[
            (
                (dataframe["pullback_long"]) &
                (dataframe["adx"] > 23) &
                (dataframe["ema50_1h"] > dataframe["ema200_1h"])
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "pullback_ma_long")


        # SHORT searah BTC (bear)
        dataframe.loc[
            (
                (dataframe["pullback_short"]) &
                (dataframe["adx"] > 23) &
                (dataframe["ema50_1h"] < dataframe["ema200_1h"])
            ),
            ["enter_short", "enter_tag"],
        ] = (1, "pullback_ma_short")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, "exit_long"] = 0
        dataframe.loc[:, "exit_short"] = 0
        return dataframe

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float,
                            rate: float, time_in_force: str, entry_tag: str,
                            side: str, **kwargs) -> bool:
        # Cek minimum leverage 20x
        try:
            import requests as _req
            symbol = pair.replace("/", "").replace(":USDT", "")
            resp = _req.get(f"https://fapi.binance.com/fapi/v1/leverageBracket?symbol={symbol}", timeout=5)
            brackets = resp.json()
            max_lev = brackets[0]["brackets"][0]["initialLeverage"]
            if max_lev < 20:
                print(f"[LevFilter] Skip {pair} — max leverage {max_lev}x < 20x")
                return False
        except Exception as e:
            print(f"[LevFilter] Error cek leverage {pair}: {e}")

        # Block entry di jam sepi
        # Load settings
        try:
            import json as _json
            with open("/freqtrade/user_data/jarvis_settings.json") as f:
                settings = _json.load(f)
        except:
            settings = {"time_filter": False, "smart_exit": False}

        # Cek session notice hanya kalau time_filter aktif
        if settings.get("time_filter", False):
            self.check_session_notice()

        if settings.get("time_filter", False) and not self.is_trading_time():
            print(f"[TimeFilter] Skip entry {pair} — jam sepi")
            return False

        try:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if dataframe is None or dataframe.empty:
                return True
            last = dataframe.iloc[-1]
            if side == "long":
                trend_score = int(last.get("bull_score", 0))
            else:
                trend_score = int(last.get("bear_score", 0))
            signal = {
                "pair": pair,
                "side": side,
                "entry_price": rate,
                "adx": float(last.get("adx", 0)),
                "rsi": float(last.get("rsi", 0)),
                "trend_score": trend_score,
            }
            if self.tg_token and self.tg_chat_id:
                send_telegram_signal(self.tg_token, self.tg_chat_id, signal)
        except Exception as e:
            print(f"[Telegram Entry] Error: {e}")
        return True

    def custom_exit(self, pair: str, trade, current_time, current_rate: float,
                    current_profit: float, **kwargs):
        # Smart exit: kalau sudah 2 jam dan profit > 0, close
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
                    "profit_pct": profit_pct * 10,
                    "reason": exit_reason,
                }
                send_telegram_exit(self.tg_token, self.tg_chat_id, exit_info)
        except Exception as e:
            print(f"[Telegram Exit] Error: {e}")
        return True
