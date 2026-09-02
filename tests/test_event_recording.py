import json

from engine.event_bus import EventBus
from engine.event_recorder import EventRecorder
from engine.events import EventType
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


def test_engine_events_can_be_recorded(tmp_path):
    path = tmp_path / "events.jsonl"

    bus = EventBus()
    recorder = EventRecorder(str(path))

    bus.subscribe(recorder.record)

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

    lines = path.read_text().splitlines()

    assert len(lines) == 3

    events = [
        json.loads(line)
        for line in lines
    ]

    assert [event["sequence"] for event in events] == [1, 2, 3]

    assert events[0]["event_type"] == "ORDER_ACCEPTED"
    assert events[1]["event_type"] == "ORDER_ACCEPTED"
    assert events[2]["event_type"] == "TRADE_EXECUTED"

    assert events[2]["buy_order_id"] == 2
    assert events[2]["sell_order_id"] == 1
    assert events[2]["price"] == 100
    assert events[2]["quantity"] == 50