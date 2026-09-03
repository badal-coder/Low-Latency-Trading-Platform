from engine.gateway import OrderGateway, OrderRequest
from engine.matching_engine import MatchingEngine
from engine.order import OrderType, Side


def test_gateway_submits_order():

    engine = MatchingEngine()
    gateway = OrderGateway(engine)

    request = OrderRequest(
        order_id=1,
        account_id=100,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        quantity=10,
        price=100,
        timestamp_ns=1,
    )

    trades = gateway.submit(request)

    assert trades == []

    book = engine.get_book("AAPL")

    assert 1 in book.orders

    order = book.orders[1]

    assert order.account_id == 100
    assert order.quantity == 10
    assert order.price == 100


def test_gateway_matches_orders():

    engine = MatchingEngine()
    gateway = OrderGateway(engine)

    gateway.submit(
        OrderRequest(
            order_id=1,
            account_id=100,
            symbol="AAPL",
            side=Side.SELL,
            order_type=OrderType.LIMIT,
            quantity=10,
            price=100,
            timestamp_ns=1,
        )
    )

    trades = gateway.submit(
        OrderRequest(
            order_id=2,
            account_id=200,
            symbol="AAPL",
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            quantity=10,
            price=100,
            timestamp_ns=2,
        )
    )

    assert len(trades) == 1

    trade = trades[0]

    assert trade.quantity == 10
    assert trade.price == 100
    assert trade.buy_order_id == 2
    assert trade.sell_order_id == 1


def test_gateway_cancel():

    engine = MatchingEngine()
    gateway = OrderGateway(engine)

    gateway.submit(
        OrderRequest(
            order_id=1,
            account_id=100,
            symbol="AAPL",
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            quantity=10,
            price=100,
            timestamp_ns=1,
        )
    )

    result = gateway.cancel(
        "AAPL",
        1,
    )

    assert result is True

    book = engine.get_book("AAPL")

    assert 1 not in book.orders