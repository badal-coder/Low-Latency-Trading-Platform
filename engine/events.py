from dataclasses import dataclass
from enum import Enum, auto

from .order import OrderType, Side


class EventType(Enum):
    ORDER_ACCEPTED = auto()
    ORDER_REJECTED = auto()
    ORDER_CANCELLED = auto()
    TRADE_EXECUTED = auto()


@dataclass(frozen=True)
class Event:
    sequence: int
    event_type: EventType
    timestamp_ns: int


@dataclass(frozen=True)
class OrderAcceptedEvent(Event):
    order_id: int
    symbol: str

    # Optional order metadata.
    #
    # Defaults are intentional for backwards compatibility with
    # older event producers/tests that only supplied order_id
    # and symbol.
    account_id: int | None = None
    side: Side | None = None
    order_type: OrderType | None = None
    price: int | None = None
    quantity: int | None = None


@dataclass(frozen=True)
class OrderRejectedEvent(Event):
    order_id: int
    symbol: str
    reason: str


@dataclass(frozen=True)
class OrderCancelledEvent(Event):
    order_id: int
    symbol: str


@dataclass(frozen=True)
class TradeExecutedEvent(Event):
    buy_order_id: int
    sell_order_id: int
    symbol: str
    price: int
    quantity: int