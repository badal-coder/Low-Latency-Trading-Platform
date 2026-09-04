from dataclasses import dataclass

from .matching_engine import MatchingEngine, Trade
from .order import Order, Side, OrderType


@dataclass(slots=True)
class OrderRequest:
    order_id: int
    account_id: int
    symbol: str
    side: Side
    order_type: OrderType
    quantity: int
    price: int
    timestamp_ns: int


class OrderGateway:
    def __init__(
        self,
        matching_engine: MatchingEngine | None = None,
    ):
        self.matching_engine = (
            matching_engine
            if matching_engine is not None
            else MatchingEngine()
        )

        # Persistent order store.
        self.orders: dict[int, Order] = {}

    def submit(
        self,
        request: OrderRequest,
    ) -> list[Trade]:

        order = Order(
            order_id=request.order_id,
            account_id=request.account_id,
            symbol=request.symbol,
            side=request.side,
            order_type=request.order_type,
            quantity=request.quantity,
            price=request.price,
            timestamp_ns=request.timestamp_ns,
        )

        self.orders[request.order_id] = order

        return self.matching_engine.submit_order(order)

    def submit_order(
        self,
        request: OrderRequest,
    ) -> list[Trade]:

        return self.submit(request)

    def cancel(
        self,
        symbol: str,
        order_id: int,
    ) -> bool:

        return self.matching_engine.cancel_order(
            symbol,
            order_id,
        )

    def cancel_order(
        self,
        symbol: str,
        order_id: int,
    ) -> bool:

        return self.cancel(symbol, order_id)

    def get_order(
        self,
        order_id: int,
    ) -> Order:

        order = self.orders.get(order_id)

        if order is None:
            raise ValueError(
                f"unknown order: {order_id}"
            )

        return order


# Compatibility alias.
Gateway = OrderGateway