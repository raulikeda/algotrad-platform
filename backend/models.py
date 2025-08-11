"""
Data Models for Home Broker Simulator
"""

from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional, List
from dataclasses import dataclass


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"


@dataclass
class BookLevel:
    """Order book level"""
    price: float
    quantity: float


@dataclass
class User:
    """User data model"""
    id: str
    cash_balance: float
    asset_balance: float


@dataclass
class Order:
    """Order data model"""
    id: str
    user_id: str
    symbol: str
    order_type: OrderType
    side: OrderSide
    quantity: float
    price: Optional[float]
    timestamp: datetime
    filled_quantity: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    
    @property
    def remaining_quantity(self) -> float:
        return self.quantity - self.filled_quantity
    
    @property
    def is_fully_filled(self) -> bool:
        return self.filled_quantity >= self.quantity
    
    def to_dict(self) -> dict:
        """Convert order to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "symbol": self.symbol,
            "order_type": self.order_type.value,
            "side": self.side.value,
            "quantity": self.quantity,
            "price": self.price,
            "timestamp": self.timestamp.isoformat(),
            "filled_quantity": self.filled_quantity,
            "remaining_quantity": self.remaining_quantity,
            "status": self.status.value,
            "is_fully_filled": self.is_fully_filled
        }


@dataclass
class Fill:
    """Fill/Trade data model"""
    id: str
    buyer_order_id: str
    seller_order_id: str
    buyer_id: str
    seller_id: str
    symbol: str
    quantity: float
    price: float
    timestamp: datetime
    
    @property
    def order_id(self) -> str:
        """Get order ID (for backward compatibility)"""
        return self.buyer_order_id
    
    def get_side_for_user(self, user_id: str) -> OrderSide:
        """Get the side from the perspective of a specific user"""
        if user_id == self.buyer_id:
            return OrderSide.BUY
        elif user_id == self.seller_id:
            return OrderSide.SELL
        else:
            # Default fallback
            return OrderSide.BUY
    
    @property
    def side(self) -> OrderSide:
        """Get side from perspective of the order (for backward compatibility)"""
        return OrderSide.BUY


@dataclass
class OrderBook:
    """Order book data model"""
    symbol: str
    bids: List[BookLevel]
    asks: List[BookLevel]
    last_price: Optional[float] = None
    timestamp: Optional[datetime] = None


class PlaceOrderRequest(BaseModel):
    """Request model for placing orders"""
    order_type: str
    side: str
    quantity: float
    price: Optional[float] = None


class UpdateOrderRequest(BaseModel):
    """Request model for updating orders"""
    price: Optional[float] = None
    quantity: Optional[float] = None
