from dataclasses import dataclass
from enum import Enum


class Side(Enum):
    BUY = 1
    SELL = 2


class OrderType(Enum):
    LIMIT = 1
    MARKET = 2


class OrderStatus(Enum):
    NEW = 1
    OPEN = 2
    PARTIALLY_FILLED = 3
    FILLED = 4
    CANCELLED = 5
    REJECTED = 6


@dataclass(slots=True)
class Order:
    order_id: int
    symbol: str
    side: Side
    order_type: OrderType
    price: int
    quantity: int
    timestamp_ns: int

    filled_quantity: int = 0
    status: OrderStatus = OrderStatus.NEW

    @property
    def remaining_quantity(self) -> int:
        return self.quantity - self.filled_quantity