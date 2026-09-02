from collections import deque
from dataclasses import dataclass
from typing import Deque

from .order import Order, Side


@dataclass
class PriceLevel:
    price: int
    orders: Deque[Order]


class OrderBook:
    def __init__(self, symbol: str):
        self.symbol = symbol

        self.bids: dict[int, PriceLevel] = {}
        self.asks: dict[int, PriceLevel] = {}

        # Fast lookup: order_id -> Order
        self.orders: dict[int, Order] = {}

    def add_order(self, order: Order) -> None:
        book = self.bids if order.side == Side.BUY else self.asks

        if order.price not in book:
            book[order.price] = PriceLevel(
                price=order.price,
                orders=deque(),
            )

        book[order.price].orders.append(order)
        self.orders[order.order_id] = order

    def remove_order(self, order_id: int) -> bool:
        order = self.orders.get(order_id)

        if order is None:
            return False

        book = self.bids if order.side == Side.BUY else self.asks
        level = book.get(order.price)

        if level is None:
            return False

        try:
            level.orders.remove(order)
        except ValueError:
            return False

        del self.orders[order_id]

        if not level.orders:
            del book[order.price]

        return True

    def best_bid(self) -> int | None:
        if not self.bids:
            return None

        return max(self.bids)

    def best_ask(self) -> int | None:
        if not self.asks:
            return None

        return min(self.asks)