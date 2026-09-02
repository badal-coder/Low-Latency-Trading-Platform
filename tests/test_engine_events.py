from engine.event_bus import EventBus
from engine.events import (
    EventType,
    OrderAcceptedEvent,
    OrderCancelledEvent,
    TradeExecutedEvent,
)
from engine.matching_engine import MatchingEngine
from engine.order import Order, OrderType, Side


def make_order(
    order_id,
    side,
    price,
    quantity,
    timestamp,
):
    return Order(
        order_id=order_id,
        symbol="BTCUSD",
        side=side,
        order_type=OrderType.LIMIT,
        price=price,
        quantity=quantity,
        timestamp_ns=timestamp,
    )


def test_order_submission_generates_event():
    bus = EventBus()
    events = []

    bus.subscribe(events.append)

    engine = MatchingEngine(bus)

    order = make_order(
        1,
        Side.BUY,
        100,
        50,
        1,
    )

    engine.submit_order(order)

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, OrderAcceptedEvent)
    assert event.event_type == EventType.ORDER_ACCEPTED
    assert event.sequence == 1
    assert event.order_id == 1
    assert event.symbol == "BTCUSD"


def test_trade_generates_event():
    bus = EventBus()
    events = []

    bus.subscribe(events.append)

    engine = MatchingEngine(bus)

    sell = make_order(
        1,
        Side.SELL,
        100,
        50,
        1,
    )

    buy = make_order(
        2,
        Side.BUY,
        100,
        50,
        2,
    )

    engine.submit_order(sell)
    engine.submit_order(buy)

    trade_events = [
        event
        for event in events
        if isinstance(event, TradeExecutedEvent)
    ]

    assert len(trade_events) == 1

    event = trade_events[0]

    assert event.buy_order_id == 2
    assert event.sell_order_id == 1
    assert event.price == 100
    assert event.quantity == 50


def test_cancel_generates_event():
    bus = EventBus()
    events = []

    bus.subscribe(events.append)

    engine = MatchingEngine(bus)

    order = make_order(
        1,
        Side.BUY,
        100,
        50,
        1,
    )

    engine.submit_order(order)

    events.clear()

    assert engine.cancel_order(
        "BTCUSD",
        1,
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, OrderCancelledEvent)
    assert event.event_type == EventType.ORDER_CANCELLED
    assert event.order_id == 1


def test_event_sequences_are_monotonic():
    bus = EventBus()
    events = []

    bus.subscribe(events.append)

    engine = MatchingEngine(bus)

    sell = make_order(
        1,
        Side.SELL,
        100,
        50,
        1,
    )

    buy = make_order(
        2,
        Side.BUY,
        100,
        50,
        2,
    )

    engine.submit_order(sell)
    engine.submit_order(buy)

    sequences = [
        event.sequence
        for event in events
    ]

    assert sequences == sorted(sequences)
    assert sequences == list(
        range(1, len(sequences) + 1)
    )
    