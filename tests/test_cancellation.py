from engine.matching_engine import MatchingEngine
from engine.order import Order, OrderType, Side


def make_order(order_id, price=100, timestamp=None):
    if timestamp is None:
        timestamp = order_id

    return Order(
        order_id=order_id,
        symbol="BTCUSD",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        price=price,
        quantity=10,
        timestamp_ns=timestamp,
    )


def test_cancel_middle_order():
    engine = MatchingEngine()

    engine.submit_order(make_order(1))
    engine.submit_order(make_order(2))
    engine.submit_order(make_order(3))

    book = engine.get_book("BTCUSD")

    assert len(book.bids[100].orders) == 3

    assert engine.cancel_order("BTCUSD", 2) is True

    assert 2 not in book.orders
    assert 2 not in book.order_nodes

    assert len(book.bids[100].orders) == 2

    first = book.bids[100].orders.peek()

    assert first is not None
    assert first.order.order_id == 1
    assert first.next is not None
    assert first.next.order.order_id == 3


def test_fifo_after_middle_cancellation():
    engine = MatchingEngine()

    engine.submit_order(make_order(1))
    engine.submit_order(make_order(2))
    engine.submit_order(make_order(3))

    engine.cancel_order("BTCUSD", 2)

    sell = Order(
        order_id=10,
        symbol="BTCUSD",
        side=Side.SELL,
        order_type=OrderType.LIMIT,
        price=100,
        quantity=20,
        timestamp_ns=10,
    )

    trades = engine.submit_order(sell)

    assert len(trades) == 2

    assert trades[0].buy_order_id == 1
    assert trades[0].quantity == 10

    assert trades[1].buy_order_id == 3
    assert trades[1].quantity == 10


def test_cancel_head():
    engine = MatchingEngine()

    engine.submit_order(make_order(1))
    engine.submit_order(make_order(2))
    engine.submit_order(make_order(3))

    assert engine.cancel_order("BTCUSD", 1) is True

    book = engine.get_book("BTCUSD")

    node = book.bids[100].orders.peek()

    assert node is not None
    assert node.order.order_id == 2
    assert node.prev is None


def test_cancel_tail():
    engine = MatchingEngine()

    engine.submit_order(make_order(1))
    engine.submit_order(make_order(2))
    engine.submit_order(make_order(3))

    assert engine.cancel_order("BTCUSD", 3) is True

    book = engine.get_book("BTCUSD")

    node = book.bids[100].orders.peek()

    assert node is not None
    assert node.order.order_id == 1
    assert node.next is not None
    assert node.next.order.order_id == 2
    assert node.next.next is None


def test_cancel_last_order_removes_price_level():
    engine = MatchingEngine()

    engine.submit_order(make_order(1))

    assert engine.cancel_order("BTCUSD", 1) is True

    book = engine.get_book("BTCUSD")

    assert 100 not in book.bids
    assert book.best_bid() is None
    assert len(book.orders) == 0
    assert len(book.order_nodes) == 0


def test_cancel_does_not_affect_other_price_levels():
    engine = MatchingEngine()

    engine.submit_order(make_order(1, price=100))
    engine.submit_order(make_order(2, price=101))
    engine.submit_order(make_order(3, price=102))

    assert engine.cancel_order("BTCUSD", 2) is True

    book = engine.get_book("BTCUSD")

    assert 100 in book.bids
    assert 101 not in book.bids
    assert 102 in book.bids

    assert book.best_bid() == 102


def test_repeated_cancel_is_safe():
    engine = MatchingEngine()

    engine.submit_order(make_order(1))

    assert engine.cancel_order("BTCUSD", 1) is True
    assert engine.cancel_order("BTCUSD", 1) is False
    assert engine.cancel_order("BTCUSD", 1) is False