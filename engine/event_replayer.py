import json

from .events import (
    EventType,
    OrderAcceptedEvent,
    OrderRejectedEvent,
    OrderCancelledEvent,
    TradeExecutedEvent,
)


class EventReplayer:
    def __init__(self):
        self.events = []

    def replay(self, path: str):
        self.events.clear()

        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                data = json.loads(line)

                event_type = EventType[data["event_type"]]

                if event_type == EventType.ORDER_ACCEPTED:
                    event = OrderAcceptedEvent(
                        sequence=data["sequence"],
                        event_type=event_type,
                        timestamp_ns=data["timestamp_ns"],
                        order_id=data["order_id"],
                        account_id=data["account_id"],
                        symbol=data["symbol"],
                        side=data["side"],
                        order_type=data["order_type"],
                        price=data["price"],
                        quantity=data["quantity"],
                    )

                elif event_type == EventType.ORDER_REJECTED:
                    event = OrderRejectedEvent(
                        sequence=data["sequence"],
                        event_type=event_type,
                        timestamp_ns=data["timestamp_ns"],
                        order_id=data["order_id"],
                        symbol=data["symbol"],
                        reason=data["reason"],
                    )

                elif event_type == EventType.ORDER_CANCELLED:
                    event = OrderCancelledEvent(
                        sequence=data["sequence"],
                        event_type=event_type,
                        timestamp_ns=data["timestamp_ns"],
                        order_id=data["order_id"],
                        symbol=data["symbol"],
                    )

                elif event_type == EventType.TRADE_EXECUTED:
                    event = TradeExecutedEvent(
                        sequence=data["sequence"],
                        event_type=event_type,
                        timestamp_ns=data["timestamp_ns"],
                        buy_order_id=data["buy_order_id"],
                        sell_order_id=data["sell_order_id"],
                        symbol=data["symbol"],
                        price=data["price"],
                        quantity=data["quantity"],
                    )

                else:
                    raise ValueError(
                        f"unsupported event type: {event_type}"
                    )

                self.events.append(event)

        return self.events