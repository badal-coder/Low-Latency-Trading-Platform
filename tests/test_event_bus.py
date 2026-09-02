from engine.event_bus import EventBus
from engine.events import (
    EventType,
    OrderAcceptedEvent,
)


def test_event_bus_publishes_event():
    bus = EventBus()

    received = []

    def handler(event):
        received.append(event)

    bus.subscribe(handler)

    event = OrderAcceptedEvent(
        sequence=1,
        event_type=EventType.ORDER_ACCEPTED,
        timestamp_ns=123,
        order_id=100,
        symbol="BTCUSD",
    )

    bus.publish(event)

    assert len(received) == 1
    assert received[0] == event


def test_multiple_handlers_receive_event():
    bus = EventBus()

    first = []
    second = []

    bus.subscribe(first.append)
    bus.subscribe(second.append)

    event = OrderAcceptedEvent(
        sequence=1,
        event_type=EventType.ORDER_ACCEPTED,
        timestamp_ns=123,
        order_id=100,
        symbol="BTCUSD",
    )

    bus.publish(event)

    assert first == [event]
    assert second == [event]