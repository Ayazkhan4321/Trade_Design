"""
Data Transfer Objects for trading operations
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class OrderDTO:
    """Data Transfer Object for orders"""
    symbol: str
    order_type: str  # 'BUY' or 'SELL'
    volume: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    remarks: str = ""
    price: Optional[float] = None  # For limit orders
    order_category: str = "market"  # 'market' or 'limit'
    timestamp: datetime = field(default_factory=datetime.now)
    order_id: Optional[str] = None


@dataclass
class SymbolDTO:
    """Data Transfer Object for symbols"""
    name: str
    sell_price: str
    buy_price: str
    change: Optional[str] = None
    change_percent: Optional[str] = None
    high: Optional[str] = None
    low: Optional[str] = None
    volume: Optional[str] = None


@dataclass
class PriceDTO:
    """Data Transfer Object for price updates"""
    symbol: str
    sell_price: float
    buy_price: float
    timestamp: datetime = field(default_factory=datetime.now)
    spread: Optional[float] = None
