from dataclasses import dataclass

from .order import Order, Side
from .order_queue import OrderNode, OrderQueue


@dataclass(slots=True)
class PriceLevel:
    price: int
    orders: OrderQueue


class OrderBook:
    def __init__(self, symbol: str):
        self.symbol = symbol

        self.bids: dict[int, PriceLevel] = {}
        self.asks: dict[int, PriceLevel] = {}

        # order_id -> Order
        self.orders: dict[int, Order] = {}

        # order_id -> OrderNode
        self.order_nodes: dict[int, OrderNode] = {}

    def add_order(self, order: Order) -> None:
        book = self.bids if order.side == Side.BUY else self.asks

        if order.price not in book:
            book[order.price] = PriceLevel(
                price=order.price,
                orders=OrderQueue(),
            )

        node = book[order.price].orders.append(order)

        self.orders[order.order_id] = order
        self.order_nodes[order.order_id] = node

    def remove_order(self, order_id: int) -> bool:
        order = self.orders.get(order_id)
        node = self.order_nodes.get(order_id)

        if order is None or node is None:
            return False

        book = self.bids if order.side == Side.BUY else self.asks
        level = book.get(order.price)

        if level is None:
            return False

        level.orders.remove(node)

        del self.orders[order_id]
        del self.order_nodes[order_id]

        if len(level.orders) == 0:
            del book[order.price]

        return True

    def pop_best_order(
        self,
        side: Side,
    ) -> Order | None:

        book = self.bids if side == Side.BUY else self.asks

        if not book:
            return None

        price = (
            max(book)
            if side == Side.BUY
            else min(book)
        )

        level = book[price]

        node = level.orders.popleft()

        if node is None:
            return None

        order = node.order

        del self.orders[order.order_id]
        del self.order_nodes[order.order_id]

        if len(level.orders) == 0:
            del book[price]

        return order

    def best_bid(self) -> int | None:
        if not self.bids:
            return None

        return max(self.bids)

    def best_ask(self) -> int | None:
        if not self.asks:
            return None

        return min(self.asks)