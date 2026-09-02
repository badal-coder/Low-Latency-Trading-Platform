from dataclasses import dataclass

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
    def __init__(self):
        self.books: dict[str, OrderBook] = {}
        self.next_trade_id = 1

    def get_book(self, symbol: str) -> OrderBook:
        if symbol not in self.books:
            self.books[symbol] = OrderBook(symbol)

        return self.books[symbol]

    def submit_order(self, order: Order) -> list[Trade]:
        book = self.get_book(order.symbol)

        if order.order_type == OrderType.MARKET:
            return self._match_market(order, book)

        return self._match_limit(order, book)

    def cancel_order(self, symbol: str, order_id: int) -> bool:
        book = self.books.get(symbol)

        if book is None:
            return False

        order = book.orders.get(order_id)

        if order is None:
            return False

        success = book.remove_order(order_id)

        if success:
            order.status = OrderStatus.CANCELLED

        return success

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

        trades = []

        while order.remaining_quantity > 0:

            if order.side == Side.BUY:
                best_price = book.best_ask()

                if best_price is None or best_price > order.price:
                    break

                level = book.asks[best_price]

            else:
                best_price = book.best_bid()

                if best_price is None or best_price < order.price:
                    break

                level = book.bids[best_price]

            while level.orders and order.remaining_quantity > 0:

                resting_order = level.orders[0]

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

                self._update_fill(order, trade_quantity)
                self._update_fill(resting_order, trade_quantity)

                if resting_order.remaining_quantity == 0:
                    level.orders.popleft()
                    del book.orders[resting_order.order_id]

            if not level.orders:
                if order.side == Side.BUY:
                    del book.asks[best_price]
                else:
                    del book.bids[best_price]

        # If the order never traded, it becomes OPEN.
        # If it traded partially, keep PARTIALLY_FILLED.
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

        trades = []

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

            while level.orders and order.remaining_quantity > 0:

                resting_order = level.orders[0]

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

                self._update_fill(order, trade_quantity)
                self._update_fill(resting_order, trade_quantity)

                if resting_order.remaining_quantity == 0:
                    level.orders.popleft()
                    del book.orders[resting_order.order_id]

            if not level.orders:
                if order.side == Side.BUY:
                    del book.asks[best_price]
                else:
                    del book.bids[best_price]

        return trades