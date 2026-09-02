from engine.order import Order, OrderType, Side
from engine.risk import RiskEngine, RiskLimits


def make_order(
    quantity=50,
    price=100,
    order_type=OrderType.LIMIT,
):
    return Order(
        order_id=1,
        symbol="BTCUSD",
        side=Side.BUY,
        order_type=order_type,
        price=price,
        quantity=quantity,
        timestamp_ns=1,
    )


def test_valid_order_passes():
    risk = RiskEngine()

    ok, reason = risk.check_order(make_order())

    assert ok is True
    assert reason is None


def test_zero_quantity_fails():
    risk = RiskEngine()

    ok, reason = risk.check_order(make_order(quantity=0))

    assert ok is False
    assert reason == "INVALID_QUANTITY"


def test_negative_quantity_fails():
    risk = RiskEngine()

    ok, reason = risk.check_order(make_order(quantity=-10))

    assert ok is False
    assert reason == "INVALID_QUANTITY"


def test_max_quantity():
    risk = RiskEngine(
        RiskLimits(max_order_quantity=100)
    )

    ok, reason = risk.check_order(make_order(quantity=101))

    assert ok is False
    assert reason == "MAX_ORDER_QUANTITY"


def test_max_notional():
    risk = RiskEngine(
        RiskLimits(max_order_notional=5_000)
    )

    ok, reason = risk.check_order(
        make_order(quantity=100, price=100)
    )

    assert ok is False
    assert reason == "MAX_ORDER_NOTIONAL"


def test_market_order_does_not_use_notional_limit():
    risk = RiskEngine(
        RiskLimits(max_order_notional=1)
    )

    ok, reason = risk.check_order(
        make_order(
            quantity=500,
            price=0,
            order_type=OrderType.MARKET,
        )
    )

    assert ok is True
    assert reason is None