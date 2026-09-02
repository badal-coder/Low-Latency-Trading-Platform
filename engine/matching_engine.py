from dataclasses import dataclass

from .event_bus import EventBus
from .events import (
    EventType,
    OrderAcceptedEvent,
    OrderCancelledEvent,
    TradeExecutedEvent,
)
from .order import Order, Side, OrderType, OrderStatus
from .order_book import OrderBook


@dataclass(slots=True)
class Trade:
    trade_id: int
    symbol: str
    price: int
    quantity: int
    buy_order_id: int
    sell_order_id: int


class MatchingEngine:
    def __init__(self, event_bus: EventBus | None = None):
        self.books: dict[str, OrderBook] = {}

        self.next_trade_id = 1
        self.next_sequence = 1

        self.event_bus = event_bus or EventBus()

    def get_book(self, symbol: str) -> OrderBook:
        if symbol not in self.books:
            self.books[symbol] = OrderBook(symbol)

        return self.books[symbol]

    def _next_event_sequence(self) -> int:
        sequence = self.next_sequence
        self.next_sequence += 1
        return sequence

    def _validate_order(self, order: Order) -> bool:
        # Quantity must be positive.
        if order.quantity <= 0:
            return False

        # Limit orders must have a positive price.
        # Market orders do not require a price.
        if (
            order.order_type == OrderType.LIMIT
            and order.price <= 0
        ):
            return False

        # Order IDs must be unique within the symbol's book.
        book = self.get_book(order.symbol)

        if order.order_id in book.orders:
            return False

        return True

    def submit_order(self, order: Order) -> list[Trade]:

        # Validate before accepting the order.
        if not self._validate_order(order):
            order.status = OrderStatus.REJECTED
            return []

        book: OrderBook = self.get_book(order.symbol)

        # Every accepted order generates an event first.
        self.event_bus.publish(
            OrderAcceptedEvent(
                sequence=self._next_event_sequence(),
                event_type=EventType.ORDER_ACCEPTED,
                timestamp_ns=order.timestamp_ns,
                order_id=order.order_id,
                symbol=order.symbol,
            )
        )

        if order.order_type == OrderType.MARKET:
            trades: list[Trade] = self._match_market(
                order,
                book,
            )
        else:
            trades: list[Trade] = self._match_limit(
                order,
                book,
            )

        return trades

    def cancel_order(
        self,
        symbol: str,
        order_id: int,
    ) -> bool:

        book = self.books.get(symbol)

        if book is None:
            return False

        order = book.orders.get(order_id)

        if order is None:
            return False

        if book.remove_order(order_id):
            order.status = OrderStatus.CANCELLED

            self.event_bus.publish(
                OrderCancelledEvent(
                    sequence=self._next_event_sequence(),
                    event_type=EventType.ORDER_CANCELLED,
                    timestamp_ns=order.timestamp_ns,
                    order_id=order_id,
                    symbol=symbol,
                )
            )

            return True

        return False

    def _create_trade(
        self,
        incoming: Order,
        resting: Order,
        quantity: int,
    ) -> Trade:

        trade = Trade(
            trade_id=self.next_trade_id,
            symbol=incoming.symbol,
            price=resting.price,
            quantity=quantity,
            buy_order_id=(
                incoming.order_id
                if incoming.side == Side.BUY
                else resting.order_id
            ),
            sell_order_id=(
                incoming.order_id
                if incoming.side == Side.SELL
                else resting.order_id
            ),
        )

        self.next_trade_id += 1

        self.event_bus.publish(
            TradeExecutedEvent(
                sequence=self._next_event_sequence(),
                event_type=EventType.TRADE_EXECUTED,
                timestamp_ns=incoming.timestamp_ns,
                buy_order_id=trade.buy_order_id,
                sell_order_id=trade.sell_order_id,
                symbol=trade.symbol,
                price=trade.price,
                quantity=trade.quantity,
            )
        )

        return trade

    def _update_fill(
        self,
        order: Order,
        quantity: int,
    ) -> None:

        order.filled_quantity += quantity

        if order.remaining_quantity == 0:
            order.status = OrderStatus.FILLED
        else:
            order.status = OrderStatus.PARTIALLY_FILLED

    def _match_limit(
        self,
        order: Order,
        book: OrderBook,
    ) -> list[Trade]:

        trades: list[Trade] = []

        while order.remaining_quantity > 0:

            if order.side == Side.BUY:
                best_price = book.best_ask()

                if (
                    best_price is None
                    or best_price > order.price
                ):
                    break

                level = book.asks[best_price]

            else:
                best_price = book.best_bid()

                if (
                    best_price is None
                    or best_price < order.price
                ):
                    break

                level = book.bids[best_price]

            while level.orders.peek() is not None:

                if order.remaining_quantity <= 0:
                    break

                node = level.orders.peek()
                resting_order = node.order

                trade_quantity = min(
                    order.remaining_quantity,
                    resting_order.remaining_quantity,
                )

                trades.append(
                    self._create_trade(
                        order,
                        resting_order,
                        trade_quantity,
                    )
                )

                self._update_fill(
                    order,
                    trade_quantity,
                )

                self._update_fill(
                    resting_order,
                    trade_quantity,
                )

                if resting_order.remaining_quantity == 0:
                    level.orders.popleft()

                    del book.orders[
                        resting_order.order_id
                    ]

                    del book.order_nodes[
                        resting_order.order_id
                    ]

            if len(level.orders) == 0:

                if order.side == Side.BUY:
                    del book.asks[best_price]
                else:
                    del book.bids[best_price]

        if order.remaining_quantity > 0:

            if order.filled_quantity == 0:
                order.status = OrderStatus.OPEN

            book.add_order(order)

        return trades

    def _match_market(
        self,
        order: Order,
        book: OrderBook,
    ) -> list[Trade]:

        trades: list[Trade] = []

        while order.remaining_quantity > 0:

            if order.side == Side.BUY:
                best_price = book.best_ask()

                if best_price is None:
                    break

                level = book.asks[best_price]

            else:
                best_price = book.best_bid()

                if best_price is None:
                    break

                level = book.bids[best_price]

            while level.orders.peek() is not None:

                if order.remaining_quantity <= 0:
                    break

                node = level.orders.peek()
                resting_order = node.order

                trade_quantity = min(
                    order.remaining_quantity,
                    resting_order.remaining_quantity,
                )

                trades.append(
                    self._create_trade(
                        order,
                        resting_order,
                        trade_quantity,
                    )
                )

                self._update_fill(
                    order,
                    trade_quantity,
                )

                self._update_fill(
                    resting_order,
                    trade_quantity,
                )

                if resting_order.remaining_quantity == 0:
                    level.orders.popleft()

                    del book.orders[
                        resting_order.order_id
                    ]

                    del book.order_nodes[
                        resting_order.order_id
                    ]

            if len(level.orders) == 0:

                if order.side == Side.BUY:
                    del book.asks[best_price]
                else:
                    del book.bids[best_price]

        return trades