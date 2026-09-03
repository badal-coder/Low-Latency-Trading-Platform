from engine.order import Order, OrderType, Side
from engine.matching_engine import MatchingEngine


def make_order(
    order_id,
    side,
    price,
    quantity,
    timestamp,
):
    return Order(
        order_id=order_id,
        account_id=1,
        symbol="BTCUSD",
        side=side,
        order_type=OrderType.LIMIT,
        price=price,
        quantity=quantity,
        timestamp_ns=timestamp,
    )


def test_basic_match():
    engine = MatchingEngine()

    sell = make_order(1, Side.SELL, 100, 50, 1)
    buy = make_order(2, Side.BUY, 100, 50, 2)

    engine.submit_order(sell)
    trades = engine.submit_order(buy)

    assert len(trades) == 1
    assert trades[0].price == 100
    assert trades[0].quantity == 50
    assert trades[0].buy_order_id == 2
    assert trades[0].sell_order_id == 1


def test_partial_fill():
    engine = MatchingEngine()

    sell = make_order(1, Side.SELL, 100, 50, 1)
    buy = make_order(2, Side.BUY, 100, 100, 2)

    engine.submit_order(sell)
    trades = engine.submit_order(buy)

    assert len(trades) == 1
    assert trades[0].quantity == 50

    book = engine.get_book("BTCUSD")

    assert book.best_bid() == 100

    node = book.bids[100].orders.peek()

    assert node is not None
    assert node.order.remaining_quantity == 50


def test_no_match():
    engine = MatchingEngine()

    sell = make_order(1, Side.SELL, 105, 50, 1)
    buy = make_order(2, Side.BUY, 100, 50, 2)

    engine.submit_order(sell)
    trades = engine.submit_order(buy)

    assert trades == []

    book = engine.get_book("BTCUSD")

    assert book.best_bid() == 100
    assert book.best_ask() == 105


def test_cancel_order():
    engine = MatchingEngine()

    buy = make_order(1, Side.BUY, 100, 50, 1)

    engine.submit_order(buy)

    success = engine.cancel_order("BTCUSD", 1)

    assert success is True

    book = engine.get_book("BTCUSD")

    assert book.best_bid() is None
    assert 1 not in book.orders


def test_cancel_unknown_order():
    engine = MatchingEngine()

    success = engine.cancel_order("BTCUSD", 999)

    assert success is False


def test_filled_order_removed_from_index():
    engine = MatchingEngine()

    sell = make_order(1, Side.SELL, 100, 50, 1)
    buy = make_order(2, Side.BUY, 100, 50, 2)

    engine.submit_order(sell)
    engine.submit_order(buy)

    book = engine.get_book("BTCUSD")

    assert 1 not in book.orders
    assert 2 not in book.orders


def test_order_becomes_open():
    engine = MatchingEngine()

    buy = make_order(1, Side.BUY, 100, 50, 1)

    engine.submit_order(buy)

    assert buy.status.name == "OPEN"
    assert buy.filled_quantity == 0
    assert buy.remaining_quantity == 50


def test_order_becomes_filled():
    engine = MatchingEngine()

    sell = make_order(1, Side.SELL, 100, 50, 1)
    buy = make_order(2, Side.BUY, 100, 50, 2)

    engine.submit_order(sell)
    engine.submit_order(buy)

    assert sell.filled_quantity == 50
    assert sell.remaining_quantity == 0
    assert sell.status.name == "FILLED"

    assert buy.filled_quantity == 50
    assert buy.remaining_quantity == 0
    assert buy.status.name == "FILLED"


def test_partial_fill_status():
    engine = MatchingEngine()

    sell = make_order(1, Side.SELL, 100, 40, 1)
    buy = make_order(2, Side.BUY, 100, 100, 2)

    engine.submit_order(sell)
    engine.submit_order(buy)

    assert sell.status.name == "FILLED"
    assert sell.filled_quantity == 40

    assert buy.status.name == "PARTIALLY_FILLED"
    assert buy.filled_quantity == 40
    assert buy.remaining_quantity == 60


def test_price_priority():
    engine = MatchingEngine()

    sell1 = make_order(1, Side.SELL, 101, 50, 1)
    sell2 = make_order(2, Side.SELL, 100, 50, 2)

    engine.submit_order(sell1)
    engine.submit_order(sell2)

    buy = make_order(3, Side.BUY, 101, 70, 3)

    trades = engine.submit_order(buy)

    assert len(trades) == 2

    assert trades[0].price == 100
    assert trades[0].quantity == 50

    assert trades[1].price == 101
    assert trades[1].quantity == 20


def test_time_priority():
    engine = MatchingEngine()

    sell1 = make_order(1, Side.SELL, 100, 50, 1)
    sell2 = make_order(2, Side.SELL, 100, 50, 2)

    engine.submit_order(sell1)
    engine.submit_order(sell2)

    buy = make_order(3, Side.BUY, 100, 60, 3)

    trades = engine.submit_order(buy)

    assert len(trades) == 2

    assert trades[0].sell_order_id == 1
    assert trades[0].quantity == 50

    assert trades[1].sell_order_id == 2
    assert trades[1].quantity == 10