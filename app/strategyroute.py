from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException

from app.strategy_request import StrategyRequest
from app.strategy_service import StrategyService
import json
import  pandas as pd

# Router tanımı
router = APIRouter()

# WebSocket bağlantılarını takip etmek için aktif bağlantılar listesi
active_connections = []

# StrategyService örneği
strategy_service = StrategyService()

@router.websocket("/ws/strategy")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint'i, kullanıcıdan gelen indikatör isteklerini dinler ve sinyalleri geri gönderir.
    """
    await websocket.accept()
    active_connections.append(websocket)
    print("WebSocket connected.")

    try:
        while True:
            # Kullanıcıdan gelen veriyi al
            data = await websocket.receive_text()
            message = json.loads(data)

            # Gelen mesajı doğrula ve işleme al
            strategy_request = StrategyRequest(**message)

            # İndikatörlere göre sinyalleri hesapla
            results = strategy_service.generate_signals(strategy_request.symbol, strategy_request.indicators)

            # Hesaplanan sonuçları WebSocket üzerinden kullanıcıya geri gönder
            await websocket.send_text(json.dumps({"signals": results}))
    except WebSocketDisconnect:
        print("WebSocket disconnected.")
        active_connections.remove(websocket)
    except Exception as e:
        print(f"Error: {e}")
        await websocket.send_text(json.dumps({"error": str(e)}))

@router.post("/strategy/signals")
async def generate_signals(request: StrategyRequest):
    """
    Kullanıcıdan gelen sembol, interval ve indikatör bilgilerine göre sinyalleri üretir.
    """
    try:
        # Tarihsel veriyi al
        price_data = strategy_service.get_historical_data(request.symbol, request.interval)
        if not price_data:  # Eğer liste boşsa
            raise HTTPException(status_code=400, detail="Yeterli veri bulunamadı.")

        # Listeyi DataFrame'e dönüştür
        df = pd.DataFrame(price_data, columns=["timestamp", "close"])
        df["close"] = pd.to_numeric(df["close"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

        # İndikatörlere göre sinyalleri hesapla
        signals = strategy_service.generate_signals(df, request.indicators)
        if not signals:
            raise HTTPException(status_code=400, detail="Sinyal hesaplanamadı.")

        return {
            "symbol": request.symbol,
            "signals": signals,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hata: {e}")

