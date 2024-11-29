from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import List, Dict
from app.strategy_service import StrategyService
import asyncio
import json
import requests
import time
import logging

# FastAPI router
router = APIRouter()

# StrategyService örneği
strategy_service = StrategyService()

# Aktif WebSocket bağlantılarını yönetmek için bir yapı
class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Yeni bir WebSocket bağlantısını kabul eder.
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Bir WebSocket bağlantısını sonlandırır.
        """
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict):
        """
        Tüm açık bağlantılara bir mesaj gönderir.
        """
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Mesaj gönderilirken hata oluştu: {e}")
                self.disconnect(connection)

# WebSocket yöneticisi örneği
websocket_manager = WebSocketManager()

@router.websocket("/ws/{symbol}/{interval}")
async def websocket_endpoint(websocket: WebSocket, symbol: str, interval: str):
    """
    Belirli bir sembol ve interval için fiyat verilerini gerçek zamanlı olarak dinleyen WebSocket endpoint'i.

    Args:
        websocket (WebSocket): WebSocket bağlantı nesnesi
        symbol (str): Takip edilecek coin sembolü (örneğin: BTCUSDT)
        interval (str): Fiyat güncelleme aralığı (örneğin: "1m", "5m", "1h")
    """
    await websocket_manager.connect(websocket)
    try:
        # Desteklenen zaman aralıkları
        interval_mapping = {
            "1m": 60,   # 1 dakika
            "5m": 300,  # 5 dakika
            "1h": 3600  # 1 saat
        }

        # Geçerli bir interval kontrolü
        interval_seconds = interval_mapping.get(interval)
        if not interval_seconds:
            await websocket.close(code=4001)
            return

        while True:
            # Binance API'den fiyat verisi alma
            price = await get_historical_data(symbol, interval)

            if not price:
                await websocket.close(code=4002)
                return

            # İndikatör ve sinyal bilgisi üretme
            indicators = {
                "rsi": {"upper_limit": 70, "lower_limit": 30, "period": 14},
                "ema": {"short_period": 9, "long_period": 21},
                "macd": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
                "sma": {"period": 14}
            }
            signal_data = strategy_service.generate_signals(price, indicators)

            # Mesaj oluşturma ve gönderme
            message = {
                "symbol": symbol,
                "price": price[-1],  # Son fiyat
                "signal_data": signal_data,
                "interval": interval
            }
            await websocket_manager.broadcast(message)

            # İlgili zaman aralığını bekle
            await asyncio.sleep(interval_seconds)

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
        print(f"Bağlantı kesildi: {symbol}")

    except Exception as e:
        print(f"Hata: {e}")
        await websocket.close(code=4003)

async def get_historical_data(symbol: str, interval: str, limit: int = 500):
    """
    Binance API'den tarihsel fiyat verilerini çeker.
    """
    url = f"https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
    retries = 3  # Yeniden deneme sayısı
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=20)
            if response.status_code == 200:
                data = response.json()
                # Fiyat verilerini sadece timestamp ve close olarak al
                price_data = [(entry[0], entry[4]) for entry in data]  # Timestamp, Close fiyatı
                return price_data
            else:
                print(f"API hatası: {response.status_code} - {response.text}")
                time.sleep(2)  # Hata durumunda bekleme
        except requests.exceptions.RequestException as e:
            print(f"Bağlantı hatası (deneme {attempt+1}/{retries}): {e}")
            time.sleep(2)  # Hata durumunda bekleme
    return None
