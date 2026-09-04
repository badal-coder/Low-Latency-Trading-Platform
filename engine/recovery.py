from .events import (
    Event,
    OrderAcceptedEvent,
    OrderCancelledEvent,
    OrderRejectedEvent,
    TradeExecutedEvent,
)


class ExchangeRecovery:
    """
    Reconstructs exchange state from the event stream.

    This first version focuses on rebuilding the event-derived state:
    - accepted orders
    - rejected orders
    - cancelled orders
    - executed trades

    It intentionally does not mutate a live Exchange yet.
    """

    def __init__(self):
        self.accepted_orders: set[int] = set()
        self.rejected_orders: dict[int, str] = {}
        self.cancelled_orders: set[int] = set()
        self.trades: list[TradeExecutedEvent] = []

    def apply(self, event: Event) -> None:
        if isinstance(event, OrderAcceptedEvent):
            self.accepted_orders.add(event.order_id)
            return

        if isinstance(event, OrderRejectedEvent):
            self.rejected_orders[event.order_id] = event.reason
            return

        if isinstance(event, OrderCancelledEvent):
            self.cancelled_orders.add(event.order_id)
            return

        if isinstance(event, TradeExecutedEvent):
            self.trades.append(event)
            return

        raise ValueError(
            f"unsupported event type: {type(event).__name__}"
        )

    def replay(self, events: list[Event]) -> None:
        for event in events:
            self.apply(event)