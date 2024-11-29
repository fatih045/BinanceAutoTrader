from pydantic import BaseModel
from typing import Dict

class StrategyRequestWithBalance(BaseModel):
    symbol: str  # Örneğin: 'BTCUSDT'
    interval: str  # Örneğin: '1h'
    indicators: Dict[str, dict]  # İndikatör parametreleri (RSI, MACD, vb.)
    balance: float  # Kullanıcının bakiyesi (Örneğin: 1000.0 USD)
