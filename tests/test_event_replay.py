from engine.event_bus import EventBus
from engine.event_recorder import EventRecorder
from engine.event_replayer import EventReplayer
from engine.events import (
    EventType,
    OrderAcceptedEvent,
    OrderCancelledEvent,
    OrderRejectedEvent,
    TradeExecutedEvent,
)
from engine.recovery import ExchangeRecovery


def test_event_replayer_replays_events(tmp_path):
    path = tmp_path / "events.jsonl"

    bus = EventBus()
    recorder = EventRecorder(str(path))

    bus.subscribe(recorder.record)

    bus.publish(
        OrderAcceptedEvent(
            sequence=1,
            event_type=EventType.ORDER_ACCEPTED,
            timestamp_ns=100,
            order_id=1,
            account_id=100,
            symbol="BTCUSD",
            side="BUY",
            order_type="LIMIT",
            price=100,
            quantity=10,
        )
    )

    bus.publish(
        TradeExecutedEvent(
            sequence=2,
            event_type=EventType.TRADE_EXECUTED,
            timestamp_ns=200,
            buy_order_id=2,
            sell_order_id=1,
            symbol="BTCUSD",
            price=100,
            quantity=10,
        )
    )

    events = EventReplayer().replay(str(path))

    assert len(events) == 2

    assert isinstance(events[0], OrderAcceptedEvent)

    assert events[0].order_id == 1
    assert events[0].account_id == 100
    assert events[0].symbol == "BTCUSD"
    assert events[0].side == "BUY"
    assert events[0].order_type == "LIMIT"
    assert events[0].price == 100
    assert events[0].quantity == 10

    assert isinstance(events[1], TradeExecutedEvent)

    assert events[1].buy_order_id == 2
    assert events[1].sell_order_id == 1
    assert events[1].price == 100
    assert events[1].quantity == 10


def test_event_replayer_preserves_sequence(tmp_path):
    path = tmp_path / "events.jsonl"

    bus = EventBus()
    recorder = EventRecorder(str(path))

    bus.subscribe(recorder.record)

    for sequence in range(1, 6):
        bus.publish(
            OrderAcceptedEvent(
                sequence=sequence,
                event_type=EventType.ORDER_ACCEPTED,
                timestamp_ns=sequence,
                order_id=sequence,
                account_id=100,
                symbol="BTCUSD",
                side="BUY",
                order_type="LIMIT",
                price=100,
                quantity=10,
            )
        )

    events = EventReplayer().replay(str(path))

    assert [event.sequence for event in events] == [
        1,
        2,
        3,
        4,
        5,
    ]


def test_event_replayer_handles_rejected_order(tmp_path):
    path = tmp_path / "events.jsonl"

    bus = EventBus()
    recorder = EventRecorder(str(path))

    bus.subscribe(recorder.record)

    bus.publish(
        OrderRejectedEvent(
            sequence=1,
            event_type=EventType.ORDER_REJECTED,
            timestamp_ns=100,
            order_id=10,
            symbol="BTCUSD",
            reason="INVALID_QUANTITY",
        )
    )

    events = EventReplayer().replay(str(path))

    assert len(events) == 1
    assert isinstance(events[0], OrderRejectedEvent)
    assert events[0].reason == "INVALID_QUANTITY"


def test_event_replayer_handles_cancelled_order(tmp_path):
    path = tmp_path / "events.jsonl"

    bus = EventBus()
    recorder = EventRecorder(str(path))

    bus.subscribe(recorder.record)

    bus.publish(
        OrderCancelledEvent(
            sequence=1,
            event_type=EventType.ORDER_CANCELLED,
            timestamp_ns=100,
            order_id=10,
            symbol="BTCUSD",
        )
    )

    events = EventReplayer().replay(str(path))

    assert len(events) == 1
    assert isinstance(events[0], OrderCancelledEvent)
    assert events[0].order_id == 10


def test_recovery_processes_multiple_events(tmp_path):
    path = tmp_path / "events.jsonl"

    bus = EventBus()
    recorder = EventRecorder(str(path))

    bus.subscribe(recorder.record)

    bus.publish(
        OrderAcceptedEvent(
            sequence=1,
            event_type=EventType.ORDER_ACCEPTED,
            timestamp_ns=100,
            order_id=1,
            account_id=100,
            symbol="BTCUSD",
            side="SELL",
            order_type="LIMIT",
            price=100,
            quantity=10,
        )
    )

    bus.publish(
        OrderAcceptedEvent(
            sequence=2,
            event_type=EventType.ORDER_ACCEPTED,
            timestamp_ns=101,
            order_id=2,
            account_id=200,
            symbol="BTCUSD",
            side="BUY",
            order_type="LIMIT",
            price=100,
            quantity=10,
        )
    )

    bus.publish(
        TradeExecutedEvent(
            sequence=3,
            event_type=EventType.TRADE_EXECUTED,
            timestamp_ns=102,
            buy_order_id=2,
            sell_order_id=1,
            symbol="BTCUSD",
            price=100,
            quantity=10,
        )
    )

    bus.publish(
        OrderCancelledEvent(
            sequence=4,
            event_type=EventType.ORDER_CANCELLED,
            timestamp_ns=103,
            order_id=2,
            symbol="BTCUSD",
        )
    )

    events = EventReplayer().replay(str(path))

    recovery = ExchangeRecovery()
    recovery.replay(events)

    assert recovery.accepted_orders == {1, 2}
    assert recovery.cancelled_orders == {2}
    assert len(recovery.trades) == 1