import pytest

from engine.order import Order, OrderType, Side, OrderStatus
from engine.matching_engine import MatchingEngine


def make_order(
    order_id=1,
    side=Side.BUY,
    order_type=OrderType.LIMIT,
    price=100,
    quantity=50,
    timestamp=1,
    symbol="BTCUSD",
):
    return Order(
        order_id=order_id,
        symbol=symbol,
        side=side,
        order_type=order_type,
        price=price,
        quantity=quantity,
        timestamp_ns=timestamp,
    )


def test_zero_quantity_is_rejected():
    engine = MatchingEngine()

    order = make_order(quantity=0)

    trades = engine.submit_order(order)

    assert trades == []
    assert order.status == OrderStatus.REJECTED
    assert order.order_id not in engine.get_book("BTCUSD").orders


def test_negative_quantity_is_rejected():
    engine = MatchingEngine()

    order = make_order(quantity=-10)

    trades = engine.submit_order(order)

    assert trades == []
    assert order.status == OrderStatus.REJECTED


def test_zero_limit_price_is_rejected():
    engine = MatchingEngine()

    order = make_order(price=0)

    trades = engine.submit_order(order)

    assert trades == []
    assert order.status == OrderStatus.REJECTED


def test_negative_limit_price_is_rejected():
    engine = MatchingEngine()

    order = make_order(price=-100)

    trades = engine.submit_order(order)

    assert trades == []
    assert order.status == OrderStatus.REJECTED


def test_market_order_does_not_require_positive_price():
    engine = MatchingEngine()

    order = make_order(
        order_type=OrderType.MARKET,
        price=0,
    )

    trades = engine.submit_order(order)

    assert trades == []
    assert order.status != OrderStatus.REJECTED


def test_duplicate_order_id_is_rejected():
    engine = MatchingEngine()

    first = make_order(order_id=1)
    duplicate = make_order(order_id=1)

    engine.submit_order(first)
    engine.submit_order(duplicate)

    assert first.status == OrderStatus.OPEN
    assert duplicate.status == OrderStatus.REJECTED


def test_rejected_order_does_not_enter_book():
    engine = MatchingEngine()

    order = make_order(quantity=0)

    engine.submit_order(order)

    book = engine.get_book("BTCUSD")

    assert order.order_id not in book.orders
    assert book.best_bid() is None
    assert book.best_ask() is None