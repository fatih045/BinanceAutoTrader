import os
import json
import pandas as pd
import requests
import ta
import logging
import time

import app


# Logger yapılandırması
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StrategyService:
    def __init__(self, log_file="transactions.json"):
        """
        StrategyService başlatıcısı
        :param log_file: İşlemlerin kaydedileceği JSON dosyasının yolu
        """
        # API URL tanımlaması
        self.api_url = "https://api.binance.com/api/v3/klines"

        # Log dosyası tanımlaması
        self.log_file = log_file
        if not os.path.exists(log_file):
            with open(log_file, 'w') as file:
                json.dump([], file)  # Başlangıçta boş bir JSON listesi

    def get_historical_data(self, symbol: str, interval: str, limit: int = 500):
        """
        Binance'ten tarihsel fiyat verilerini çeker ve sadece 'timestamp' ve 'close' fiyatını döner.
        """
        try:
            params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
            retries = 3  # Yeniden deneme sayısı
            for attempt in range(retries):
                try:
                    response = requests.get(self.api_url, params=params, timeout=20)
                    if response.status_code == 200:
                        # Veri işleme
                        data = response.json()
                        # Fiyat ve zaman damgası verilerini alıyoruz
                        price_data = [(entry[0], entry[4]) for entry in data]  # [timestamp, close]
                        return price_data
                    else:
                        logger.error(f"Binance API hatası: {response.status_code} - {response.text}")
                        break
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Bağlantı denemesi {attempt + 1}/{retries} başarısız. Hata: {e}")
                    time.sleep(2)  # Yeniden denemeden önce bekleme
            return None
        except Exception as e:
            logger.error(f"Binance API bağlantı hatası: {e}")
            return None

    # def generate_signals(self, price_data: list, indicators: dict):
    #     """
    #     Kullanıcı tarafından gönderilen indikatörlere göre sinyalleri hesaplar.
    #     """
    #     signals = {}
    #     try:
    #         if not isinstance(indicators, dict):
    #             raise ValueError("Indicators parametresi dict formatında olmalıdır.")
    #
    #         # Price data'yı DataFrame'e dönüştürme
    #         df = pd.DataFrame(price_data, columns=["timestamp", "close"])
    #         df["close"] = pd.to_numeric(df["close"])
    #         df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    #
    #         # RSI
    #         if "rsi" in indicators:
    #             rsi_params = indicators["rsi"]
    #             if not all(key in rsi_params for key in ["period", "upper_limit", "lower_limit"]):
    #                 raise ValueError("RSI parametreleri eksik: period, upper_limit, lower_limit gerekli.")
    #             rsi = ta.momentum.RSIIndicator(df["close"], window=rsi_params["period"]).rsi()
    #             if rsi.iloc[-1] > rsi_params["upper_limit"]:
    #                 signals["rsi_signal"] = "sell"
    #             elif rsi.iloc[-1] < rsi_params["lower_limit"]:
    #                 signals["rsi_signal"] = "buy"
    #             else:
    #                 signals["rsi_signal"] = "hold"
    #
    #         # EMA
    #         if "ema" in indicators:
    #             ema_params = indicators["ema"]
    #             if not all(key in ema_params for key in ["short_period", "long_period"]):
    #                 raise ValueError("EMA parametreleri eksik: short_period ve long_period gerekli.")
    #             ema_short = ta.trend.EMAIndicator(df["close"], window=ema_params["short_period"]).ema_indicator()
    #             ema_long = ta.trend.EMAIndicator(df["close"], window=ema_params["long_period"]).ema_indicator()
    #             signals["ema_signal"] = "buy" if ema_short.iloc[-1] > ema_long.iloc[-1] else "sell"
    #
    #         # SMA
    #         if "sma" in indicators:
    #             sma_params = indicators["sma"]
    #             if "period" not in sma_params:
    #                 raise ValueError("SMA parametreleri eksik: period gerekli.")
    #             sma = ta.trend.SMAIndicator(df["close"], window=sma_params["period"]).sma_indicator()
    #             signals["sma_signal"] = "buy" if df["close"].iloc[-1] > sma.iloc[-1] else "sell"
    #
    #         # MACD
    #         if "macd" in indicators:
    #             macd_params = indicators["macd"]
    #             if not all(key in macd_params for key in ["fast_period", "slow_period", "signal_period"]):
    #                 raise ValueError("MACD parametreleri eksik: fast_period, slow_period, signal_period gerekli.")
    #             macd = ta.trend.MACD(
    #                 df["close"],
    #                 window_fast=macd_params["fast_period"],
    #                 window_slow=macd_params["slow_period"],
    #                 window_sign=macd_params["signal_period"]
    #             )
    #             signals["macd_signal"] = "buy" if macd.macd().iloc[-1] > macd.macd_signal().iloc[-1] else "sell"
    #
    #         # Bollinger Bands
    #         if "bollinger_bands" in indicators:
    #             bb_params = indicators["bollinger_bands"]
    #             if not all(key in bb_params for key in ["period", "std_dev"]):
    #                 raise ValueError("Bollinger Bands parametreleri eksik: period ve std_dev gerekli.")
    #             bb = ta.volatility.BollingerBands(df["close"], window=bb_params["period"], window_dev=bb_params["std_dev"])
    #             upper_band = bb.bollinger_hband()
    #             lower_band = bb.bollinger_lband()
    #             if df["close"].iloc[-1] > upper_band.iloc[-1]:
    #                 signals["bollinger_bands_signal"] = "sell"
    #             elif df["close"].iloc[-1] < lower_band.iloc[-1]:
    #                 signals["bollinger_bands_signal"] = "buy"
    #             else:
    #                 signals["bollinger_bands_signal"] = "hold"
    #
    #         # Nihai Alım-Satım Kararı
    #         decision = self.generate_final_decision(signals)
    #         signals["final_decision"] = decision
    #
    #         return signals
    #
    #     except ValueError as e:
    #         logger.error(f"Değer hatası: {e}")
    #     except Exception as e:
    #         logger.error(f"Sinyal üretim hatası: {e}")
    #     return None
    def generate_signal_with_balance(self, price_data: list, indicators: dict, balance: float):
        """
        Kullanıcı tarafından gönderilen indikatörlere göre sinyalleri hesaplar,
        mevcut bakiyeye göre alım-satım kararlarını oluşturur ve işlemleri JSON dosyasına kaydeder.

        :param price_data: Tarihsel fiyat verileri
        :param indicators: Kullanıcı tarafından belirtilen indikatör parametreleri
        :param balance: Mevcut toplam bakiye (alım/satım için kullanılacak)
        """
        signals = {}
        try:
            # Price data'yı DataFrame'e dönüştürme
            df = pd.DataFrame(price_data, columns=["timestamp", "close"])
            df["close"] = pd.to_numeric(df["close"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

            # İndikatörlere göre sinyalleri hesaplama
            # RSI
            if "rsi" in indicators:
                rsi_params = indicators["rsi"]
                if not all(key in rsi_params for key in ["period", "upper_limit", "lower_limit"]):
                    raise ValueError("RSI parametreleri eksik: period, upper_limit, lower_limit gerekli.")
                rsi = ta.momentum.RSIIndicator(df["close"], window=rsi_params["period"]).rsi()
                signals["rsi_signal"] = "sell" if rsi.iloc[-1] > rsi_params["upper_limit"] else (
                    "buy" if rsi.iloc[-1] < rsi_params["lower_limit"] else "hold"
                )

            # EMA
            if "ema" in indicators:
                ema_params = indicators["ema"]
                if not all(key in ema_params for key in ["short_period", "long_period"]):
                    raise ValueError("EMA parametreleri eksik: short_period ve long_period gerekli.")
                ema_short = ta.trend.EMAIndicator(df["close"], window=ema_params["short_period"]).ema_indicator()
                ema_long = ta.trend.EMAIndicator(df["close"], window=ema_params["long_period"]).ema_indicator()
                signals["ema_signal"] = "buy" if ema_short.iloc[-1] > ema_long.iloc[-1] else "sell"

            # SMA
            if "sma" in indicators:
                sma_params = indicators["sma"]
                if "period" not in sma_params:
                    raise ValueError("SMA parametreleri eksik: period gerekli.")
                sma = ta.trend.SMAIndicator(df["close"], window=sma_params["period"]).sma_indicator()
                signals["sma_signal"] = "buy" if df["close"].iloc[-1] > sma.iloc[-1] else "sell"

            # MACD
            if "macd" in indicators:
                macd_params = indicators["macd"]
                if not all(key in macd_params for key in ["fast_period", "slow_period", "signal_period"]):
                    raise ValueError("MACD parametreleri eksik: fast_period, slow_period, signal_period gerekli.")
                macd = ta.trend.MACD(
                    df["close"],
                    window_fast=macd_params["fast_period"],
                    window_slow=macd_params["slow_period"],
                    window_sign=macd_params["signal_period"]
                )
                signals["macd_signal"] = "buy" if macd.macd().iloc[-1] > macd.macd_signal().iloc[-1] else "sell"

            # Bollinger Bands
            if "bollinger_bands" in indicators:
                bb_params = indicators["bollinger_bands"]
                if not all(key in bb_params for key in ["period", "std_dev"]):
                    raise ValueError("Bollinger Bands parametreleri eksik: period ve std_dev gerekli.")
                bb = ta.volatility.BollingerBands(df["close"], window=bb_params["period"], window_dev=bb_params["std_dev"])
                upper_band = bb.bollinger_hband()
                lower_band = bb.bollinger_lband()
                signals["bollinger_bands_signal"] = "sell" if df["close"].iloc[-1] > upper_band.iloc[-1] else (
                    "buy" if df["close"].iloc[-1] < lower_band.iloc[-1] else "hold"
                )

            # Nihai Alım-Satım Kararı
            decision = self.generate_final_decision(signals)
            signals["final_decision"] = decision

            # İşlem Kararı ve Bakiye Güncelleme
            transaction = {
                "timestamp": str(df["timestamp"].iloc[-1]),
                "decision": decision,
                "balance": balance,
            }

            current_price = df["close"].iloc[-1]
            if decision == "buy":
                quantity = balance / current_price  # Tüm bakiye ile alım
                balance = 0  # Bakiye tamamen kullanılır
                transaction["quantity"] = quantity
                transaction["price"] = current_price
                transaction["new_balance"] = balance
            elif decision == "sell":
                # Satış durumunda bir varlığınız varsa satışı yaparak güncellenmiş bakiye hesaplanabilir.
                quantity = balance / current_price  # Tüm miktarı satış yap
                balance += quantity * current_price
                transaction["quantity"] = quantity
                transaction["price"] = current_price
                transaction["new_balance"] = balance

            # İşlemi JSON dosyasına kaydet
            self.log_transaction(transaction)

            return signals

        except ValueError as e:
            logger.error(f"Değer hatası: {e}")
        except Exception as e:
            logger.error(f"Sinyal üretim hatası: {e}")
        return None


    # Başlangıçta boş bir JSON listesi

    def log_transaction(self, transaction):
        """
        İşlemi JSON dosyasına kaydeder.
        :param transaction: İşlem bilgilerini içeren dict
        """
        try:
            with open(self.log_file, 'r+') as file:
                data = json.load(file)
                data.append(transaction)
                file.seek(0)
                json.dump(data, file, indent=4)
        except Exception as e:
            logger.error(f"İşlem kaydı sırasında hata: {e}")

    def generate_signal_with_balance(self, price_data: list, indicators: dict, balance: float):
        """
        Kullanıcı tarafından gönderilen indikatörlere göre sinyalleri hesaplar,
        mevcut bakiyeye göre alım-satım kararlarını oluşturur ve işlemleri JSON dosyasına kaydeder.

        :param price_data: Tarihsel fiyat verileri
        :param indicators: Kullanıcı tarafından belirtilen indikatör parametreleri
        :param balance: Mevcut toplam bakiye (alım/satım için kullanılacak)
        """
        signals = {}
        try:
            # Price data'yı DataFrame'e dönüştürme
            df = pd.DataFrame(price_data, columns=["timestamp", "close"])
            df["close"] = pd.to_numeric(df["close"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

            # İndikatörlere göre sinyalleri hesaplama
            # RSI
            if "rsi" in indicators:
                rsi_params = indicators["rsi"]
                if not all(key in rsi_params for key in ["period", "upper_limit", "lower_limit"]):
                    raise ValueError("RSI parametreleri eksik: period, upper_limit, lower_limit gerekli.")
                rsi = ta.momentum.RSIIndicator(df["close"], window=rsi_params["period"]).rsi()
                if rsi.iloc[-1] > rsi_params["upper_limit"]:
                    signals["rsi_signal"] = "sell"
                elif rsi.iloc[-1] < rsi_params["lower_limit"]:
                    signals["rsi_signal"] = "buy"
                else:
                    signals["rsi_signal"] = "hold"

            # EMA
            if "ema" in indicators:
                ema_params = indicators["ema"]
                if not all(key in ema_params for key in ["short_period", "long_period"]):
                    raise ValueError("EMA parametreleri eksik: short_period ve long_period gerekli.")
                ema_short = ta.trend.EMAIndicator(df["close"], window=ema_params["short_period"]).ema_indicator()
                ema_long = ta.trend.EMAIndicator(df["close"], window=ema_params["long_period"]).ema_indicator()
                signals["ema_signal"] = "buy" if ema_short.iloc[-1] > ema_long.iloc[-1] else "sell"

            # SMA
            if "sma" in indicators:
                sma_params = indicators["sma"]
                if "period" not in sma_params:
                    raise ValueError("SMA parametreleri eksik: period gerekli.")
                sma = ta.trend.SMAIndicator(df["close"], window=sma_params["period"]).sma_indicator()
                signals["sma_signal"] = "buy" if df["close"].iloc[-1] > sma.iloc[-1] else "sell"

            # MACD
            if "macd" in indicators:
                macd_params = indicators["macd"]
                if not all(key in macd_params for key in ["fast_period", "slow_period", "signal_period"]):
                    raise ValueError("MACD parametreleri eksik: fast_period, slow_period, signal_period gerekli.")
                macd = ta.trend.MACD(
                    df["close"],
                    window_fast=macd_params["fast_period"],
                    window_slow=macd_params["slow_period"],
                    window_sign=macd_params["signal_period"]
                )
                signals["macd_signal"] = "buy" if macd.macd().iloc[-1] > macd.macd_signal().iloc[-1] else "sell"

            # Bollinger Bands
            if "bollinger_bands" in indicators:
                bb_params = indicators["bollinger_bands"]
                if not all(key in bb_params for key in ["period", "std_dev"]):
                    raise ValueError("Bollinger Bands parametreleri eksik: period ve std_dev gerekli.")
                bb = ta.volatility.BollingerBands(df["close"], window=bb_params["period"], window_dev=bb_params["std_dev"])
                upper_band = bb.bollinger_hband()
                lower_band = bb.bollinger_lband()
                if df["close"].iloc[-1] > upper_band.iloc[-1]:
                    signals["bollinger_bands_signal"] = "sell"
                elif df["close"].iloc[-1] < lower_band.iloc[-1]:
                    signals["bollinger_bands_signal"] = "buy"
                else:
                    signals["bollinger_bands_signal"] = "hold"

            # Nihai Alım-Satım Kararı
            decision = self.generate_final_decision(signals)
            signals["final_decision"] = decision

            # İşlem Kararı ve Bakiye
            transaction = {
                "timestamp": str(df["timestamp"].iloc[-1]),
                "decision": decision,
                "balance": balance,
            }

            if decision == "buy":
                current_price = df["close"].iloc[-1]
                quantity = balance / current_price
                transaction["quantity"] = quantity
                transaction["price"] = current_price
            elif decision == "sell":
                transaction["quantity"] = None  # Satış miktarını buraya ekleyebilirsiniz.

            # İşlemi JSON dosyasına kaydet
            self.log_transaction(transaction)

            return signals

        except ValueError as e:
            logger.error(f"Değer hatası: {e}")
        except Exception as e:
            logger.error(f"Sinyal üretim hatası: {e}")
        return None

    def generate_final_decision(self, signals: dict):
        """
        Tüm sinyallerden genel bir alım-satım kararı üretir.
        """
        buy_signals = sum(1 for signal in signals.values() if signal == "buy")
        sell_signals = sum(1 for signal in signals.values() if signal == "sell")
        hold_signals = sum(1 for signal in signals.values() if signal == "hold")

        # Strateji: Alım-Satım-Hold mantığı
        if buy_signals > sell_signals and buy_signals >= hold_signals:
            return "buy"
        elif sell_signals > buy_signals and sell_signals >= hold_signals:
            return "sell"
        else:
            return "hold"
