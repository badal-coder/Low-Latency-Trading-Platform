from engine.order import Order, OrderType, Side
from engine.matching_engine import MatchingEngine


def make_order(
    order_id,
    side,
    price,
    quantity,
    timestamp,
    order_type=OrderType.LIMIT,
):
    return Order(
        order_id=order_id,
        symbol="BTCUSD",
        side=side,
        order_type=order_type,
        price=price,
        quantity=quantity,
        timestamp_ns=timestamp,
    )


def test_market_buy_matches_best_ask():
    engine = MatchingEngine()

    sell = make_order(
        1,
        Side.SELL,
        100,
        50,
        1,
    )

    engine.submit_order(sell)

    buy = make_order(
        2,
        Side.BUY,
        0,
        50,
        2,
        OrderType.MARKET,
    )

    trades = engine.submit_order(buy)

    assert len(trades) == 1
    assert trades[0].price == 100
    assert trades[0].quantity == 50
    assert trades[0].buy_order_id == 2
    assert trades[0].sell_order_id == 1

    assert buy.status.name == "FILLED"
    assert buy.remaining_quantity == 0


def test_market_sell_matches_best_bid():
    engine = MatchingEngine()

    buy = make_order(
        1,
        Side.BUY,
        100,
        50,
        1,
    )

    engine.submit_order(buy)

    sell = make_order(
        2,
        Side.SELL,
        0,
        50,
        2,
        OrderType.MARKET,
    )

    trades = engine.submit_order(sell)

    assert len(trades) == 1
    assert trades[0].price == 100
    assert trades[0].quantity == 50
    assert trades[0].buy_order_id == 1
    assert trades[0].sell_order_id == 2

    assert sell.status.name == "FILLED"
    assert sell.remaining_quantity == 0


def test_market_buy_consumes_multiple_price_levels():
    engine = MatchingEngine()

    sell1 = make_order(
        1,
        Side.SELL,
        101,
        50,
        1,
    )

    sell2 = make_order(
        2,
        Side.SELL,
        100,
        30,
        2,
    )

    sell3 = make_order(
        3,
        Side.SELL,
        102,
        40,
        3,
    )

    engine.submit_order(sell1)
    engine.submit_order(sell2)
    engine.submit_order(sell3)

    buy = make_order(
        4,
        Side.BUY,
        0,
        100,
        4,
        OrderType.MARKET,
    )

    trades = engine.submit_order(buy)

    assert len(trades) == 3

    # Cheapest ask first.
    assert trades[0].price == 100
    assert trades[0].quantity == 30

    assert trades[1].price == 101
    assert trades[1].quantity == 50

    assert trades[2].price == 102
    assert trades[2].quantity == 20

    assert buy.filled_quantity == 100
    assert buy.remaining_quantity == 0
    assert buy.status.name == "FILLED"


def test_market_sell_consumes_multiple_price_levels():
    engine = MatchingEngine()

    buy1 = make_order(
        1,
        Side.BUY,
        99,
        40,
        1,
    )

    buy2 = make_order(
        2,
        Side.BUY,
        100,
        30,
        2,
    )

    buy3 = make_order(
        3,
        Side.BUY,
        98,
        50,
        3,
    )

    engine.submit_order(buy1)
    engine.submit_order(buy2)
    engine.submit_order(buy3)

    sell = make_order(
        4,
        Side.SELL,
        0,
        60,
        4,
        OrderType.MARKET,
    )

    trades = engine.submit_order(sell)

    assert len(trades) == 2

    # Highest bid first.
    assert trades[0].price == 100
    assert trades[0].quantity == 30

    assert trades[1].price == 99
    assert trades[1].quantity == 30

    assert sell.filled_quantity == 60
    assert sell.remaining_quantity == 0
    assert sell.status.name == "FILLED"


def test_market_order_partial_fill_when_liquidity_is_insufficient():
    engine = MatchingEngine()

    sell = make_order(
        1,
        Side.SELL,
        100,
        40,
        1,
    )

    engine.submit_order(sell)

    buy = make_order(
        2,
        Side.BUY,
        0,
        100,
        2,
        OrderType.MARKET,
    )

    trades = engine.submit_order(buy)

    assert len(trades) == 1
    assert trades[0].quantity == 40

    assert buy.filled_quantity == 40
    assert buy.remaining_quantity == 60
    assert buy.status.name == "PARTIALLY_FILLED"


def test_market_order_on_empty_book():
    engine = MatchingEngine()

    buy = make_order(
        1,
        Side.BUY,
        0,
        100,
        1,
        OrderType.MARKET,
    )

    trades = engine.submit_order(buy)

    assert trades == []

    assert buy.filled_quantity == 0
    assert buy.remaining_quantity == 100


def test_market_buy_removes_consumed_orders():
    engine = MatchingEngine()

    sell = make_order(
        1,
        Side.SELL,
        100,
        50,
        1,
    )

    engine.submit_order(sell)

    buy = make_order(
        2,
        Side.BUY,
        0,
        50,
        2,
        OrderType.MARKET,
    )

    engine.submit_order(buy)

    book = engine.get_book("BTCUSD")

    assert 1 not in book.orders
    assert book.best_ask() is None


def test_market_order_does_not_rest_in_order_book():
    engine = MatchingEngine()

    buy = make_order(
        1,
        Side.BUY,
        0,
        100,
        1,
        OrderType.MARKET,
    )

    engine.submit_order(buy)

    book = engine.get_book("BTCUSD")

    assert 1 not in book.orders
    assert book.best_bid() is None
    assert book.best_ask() is None