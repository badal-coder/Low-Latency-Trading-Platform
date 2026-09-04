from engine.exchange import Exchange
from engine.gateway import OrderRequest
from engine.order import OrderType, Side


def test_exchange_settles_trade():

    exchange = Exchange()

    buyer = exchange.create_account(
        account_id=1,
        initial_cash=10_000,
    )

    seller = exchange.create_account(
        account_id=2,
        initial_cash=0,
    )

    # Seller must own the inventory before placing a SELL order.
    seller.update_position(
        "AAPL",
        10,
    )

    exchange.submit_order(
        OrderRequest(
            order_id=1,
            account_id=2,
            symbol="AAPL",
            side=Side.SELL,
            order_type=OrderType.LIMIT,
            quantity=10,
            price=100,
            timestamp_ns=1,
        )
    )

    trades = exchange.submit_order(
        OrderRequest(
            order_id=2,
            account_id=1,
            symbol="AAPL",
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            quantity=10,
            price=100,
            timestamp_ns=2,
        )
    )

    assert len(trades) == 1

    assert buyer.cash == 9_000
    assert seller.cash == 1_000

    assert buyer.get_position("AAPL") == 10
    assert seller.get_position("AAPL") == 0


def test_exchange_rejects_unknown_account():

    exchange = Exchange()

    try:
        exchange.submit_order(
            OrderRequest(
                order_id=1,
                account_id=999,
                symbol="AAPL",
                side=Side.BUY,
                order_type=OrderType.LIMIT,
                quantity=10,
                price=100,
                timestamp_ns=1,
            )
        )

        assert False

    except ValueError as error:
        assert str(error) == "account does not exist"


def test_exchange_can_cancel_order():

    exchange = Exchange()

    exchange.create_account(
        account_id=1,
        initial_cash=10_000,
    )

    exchange.submit_order(
        OrderRequest(
            order_id=1,
            account_id=1,
            symbol="AAPL",
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            quantity=10,
            price=100,
            timestamp_ns=1,
        )
    )

    result = exchange.cancel_order(
        "AAPL",
        1,
    )

    assert result is True

    order = exchange.gateway.get_order(1)

    assert order.status.name == "CANCELLED"


def test_exchange_buy_reserves_cash():

    exchange = Exchange()

    buyer = exchange.create_account(
        account_id=1,
        initial_cash=10_000,
    )

    exchange.submit_order(
        OrderRequest(
            order_id=1,
            account_id=1,
            symbol="AAPL",
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            quantity=50,
            price=100,
            timestamp_ns=1,
        )
    )

    assert buyer.cash == 10_000
    assert buyer.reserved_cash == 5_000


def test_exchange_buy_reservation_released_on_cancel():

    exchange = Exchange()

    buyer = exchange.create_account(
        account_id=1,
        initial_cash=10_000,
    )

    exchange.submit_order(
        OrderRequest(
            order_id=1,
            account_id=1,
            symbol="AAPL",
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            quantity=50,
            price=100,
            timestamp_ns=1,
        )
    )

    assert buyer.reserved_cash == 5_000

    result = exchange.cancel_order(
        "AAPL",
        1,
    )

    assert result is True
    assert buyer.reserved_cash == 0
    assert buyer.cash == 10_000


def test_exchange_buy_rejects_insufficient_cash():

    exchange = Exchange()

    exchange.create_account(
        account_id=1,
        initial_cash=1_000,
    )

    try:
        exchange.submit_order(
            OrderRequest(
                order_id=1,
                account_id=1,
                symbol="AAPL",
                side=Side.BUY,
                order_type=OrderType.LIMIT,
                quantity=20,
                price=100,
                timestamp_ns=1,
            )
        )

        assert False

    except ValueError as error:
        assert str(error) == "insufficient available cash"


def test_exchange_sell_requires_inventory():

    exchange = Exchange()

    exchange.create_account(
        account_id=1,
        initial_cash=10_000,
    )

    try:
        exchange.submit_order(
            OrderRequest(
                order_id=1,
                account_id=1,
                symbol="AAPL",
                side=Side.SELL,
                order_type=OrderType.LIMIT,
                quantity=10,
                price=100,
                timestamp_ns=1,
            )
        )

        assert False

    except ValueError as error:
        assert str(error) == "insufficient available position"