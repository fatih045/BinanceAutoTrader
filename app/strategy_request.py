from pydantic import BaseModel
from typing import Dict

class StrategyRequest(BaseModel):
    symbol: str  # Tek sembol
    interval: str  # Örneğin: "1m", "5m"
    indicators: Dict[str, Dict]  # Kullanıcı tarafından gönderilen indikatörler ve parametreler
