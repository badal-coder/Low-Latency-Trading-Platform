from dataclasses import dataclass
from enum import Enum


class Side(Enum):
    BUY = 1
    SELL = 2


class OrderType(Enum):
    LIMIT = 1
    MARKET = 2


class OrderStatus(Enum):
    OPEN = 1
    PARTIALLY_FILLED = 2
    FILLED = 3
    CANCELLED = 4
    REJECTED = 5


@dataclass(slots=True)
class Order:
    order_id: int
    symbol: str
    side: Side
    order_type: OrderType
    price: int
    quantity: int
    timestamp_ns: int
    account_id: int = 0

    filled_quantity: int = 0
    status: OrderStatus = OrderStatus.OPEN

    @property
    def remaining_quantity(self) -> int:
        return self.quantity - self.filled_quantity

    def fill(self, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("fill quantity must be positive")

        if quantity > self.remaining_quantity:
            raise ValueError("fill quantity exceeds remaining quantity")

        self.filled_quantity += quantity

        if self.filled_quantity == self.quantity:
            self.status = OrderStatus.FILLED
        else:
            self.status = OrderStatus.PARTIALLY_FILLED

    def cancel(self) -> None:
        if self.status == OrderStatus.FILLED:
            return

        self.status = OrderStatus.CANCELLED