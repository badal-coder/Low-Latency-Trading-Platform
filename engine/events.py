from dataclasses import dataclass
from enum import Enum, auto


class EventType(Enum):
    ORDER_ACCEPTED = auto()
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