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


def test_recovery_rebuilds_accepted_orders(tmp_path):
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
            symbol="BTCUSD",
        )
    )

    events = EventReplayer().replay(str(path))

    recovery = ExchangeRecovery()
    recovery.replay(events)

    assert recovery.accepted_orders == {1}


def test_recovery_rebuilds_rejected_orders(tmp_path):
    path = tmp_path / "events.jsonl"

    bus = EventBus()
    recorder = EventRecorder(str(path))
    bus.subscribe(recorder.record)

    bus.publish(
        OrderRejectedEvent(
            sequence=1,
            event_type=EventType.ORDER_REJECTED,
            timestamp_ns=100,
            order_id=1,
            symbol="BTCUSD",
            reason="INVALID_QUANTITY",
        )
    )

    events = EventReplayer().replay(str(path))

    recovery = ExchangeRecovery()
    recovery.replay(events)

    assert recovery.rejected_orders == {
        1: "INVALID_QUANTITY"
    }


def test_recovery_rebuilds_cancelled_orders(tmp_path):
    path = tmp_path / "events.jsonl"

    bus = EventBus()
    recorder = EventRecorder(str(path))
    bus.subscribe(recorder.record)

    bus.publish(
        OrderCancelledEvent(
            sequence=1,
            event_type=EventType.ORDER_CANCELLED,
            timestamp_ns=100,
            order_id=1,
            symbol="BTCUSD",
        )
    )

    events = EventReplayer().replay(str(path))

    recovery = ExchangeRecovery()
    recovery.replay(events)

    assert recovery.cancelled_orders == {1}


def test_recovery_rebuilds_trades(tmp_path):
    path = tmp_path / "events.jsonl"

    bus = EventBus()
    recorder = EventRecorder(str(path))
    bus.subscribe(recorder.record)

    bus.publish(
        TradeExecutedEvent(
            sequence=1,
            event_type=EventType.TRADE_EXECUTED,
            timestamp_ns=100,
            buy_order_id=2,
            sell_order_id=1,
            symbol="BTCUSD",
            price=100,
            quantity=10,
        )
    )

    events = EventReplayer().replay(str(path))

    recovery = ExchangeRecovery()
    recovery.replay(events)

    assert len(recovery.trades) == 1

    trade = recovery.trades[0]

    assert trade.buy_order_id == 2
    assert trade.sell_order_id == 1
    assert trade.symbol == "BTCUSD"
    assert trade.price == 100
    assert trade.quantity == 10


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
            symbol="BTCUSD",
        )
    )

    bus.publish(
        OrderAcceptedEvent(
            sequence=2,
            event_type=EventType.ORDER_ACCEPTED,
            timestamp_ns=101,
            order_id=2,
            symbol="BTCUSD",
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