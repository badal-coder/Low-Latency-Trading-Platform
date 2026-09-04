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

        # Cached best prices.
        # Avoids max(bids) / min(asks) on every match.
        self._best_bid: int | None = None
        self._best_ask: int | None = None

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

        # Update cached best price.
        if order.side == Side.BUY:
            if self._best_bid is None or order.price > self._best_bid:
                self._best_bid = order.price

        else:
            if self._best_ask is None or order.price < self._best_ask:
                self._best_ask = order.price

    def remove_order(self, order_id: int) -> bool:
        """
        General cancellation path.

        Uses the order_id -> node mapping so an order can be
        removed from the middle of a FIFO queue in O(1).
        """
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

            # Recalculate only when the best price disappears.
            if order.side == Side.BUY:
                if self._best_bid == order.price:
                    self._best_bid = (
                        max(self.bids)
                        if self.bids
                        else None
                    )
            else:
                if self._best_ask == order.price:
                    self._best_ask = (
                        min(self.asks)
                        if self.asks
                        else None
                    )

        return True

    def remove_filled_order(
        self,
        level: PriceLevel,
        order: Order,
    ) -> None:
        """
        Fast path for the matching engine.

        The filled order is always at the head of its price-level
        queue, so we can remove it directly.
        """
        node = level.orders.popleft()

        if node is None:
            return

        del self.orders[order.order_id]
        del self.order_nodes[order.order_id]

        if len(level.orders) == 0:
            book = (
                self.bids
                if order.side == Side.BUY
                else self.asks
            )

            del book[order.price]

            # The best price disappeared, so find the new one.
            if order.side == Side.BUY:
                self._best_bid = (
                    max(self.bids)
                    if self.bids
                    else None
                )
            else:
                self._best_ask = (
                    min(self.asks)
                    if self.asks
                    else None
                )

    def pop_best_order(
        self,
        side: Side,
    ) -> Order | None:

        book = (
            self.bids
            if side == Side.BUY
            else self.asks
        )

        if not book:
            return None

        price = (
            self._best_bid
            if side == Side.BUY
            else self._best_ask
        )

        if price is None:
            return None

        level = book[price]

        node = level.orders.popleft()

        if node is None:
            return None

        order = node.order

        del self.orders[order.order_id]
        del self.order_nodes[order.order_id]

        if len(level.orders) == 0:
            del book[price]

            if side == Side.BUY:
                self._best_bid = (
                    max(self.bids)
                    if self.bids
                    else None
                )
            else:
                self._best_ask = (
                    min(self.asks)
                    if self.asks
                    else None
                )

        return order

    def best_bid(self) -> int | None:
        return self._best_bid

    def best_ask(self) -> int | None:
        return self._best_ask