import pytest

from engine.exchange import Exchange
from engine.gateway import OrderRequest
from engine.order import OrderType, Side


def make_request(
    order_id,
    account_id,
    side,
    quantity,
    price=100,
):
    return OrderRequest(
        order_id=order_id,
        account_id=account_id,
        symbol="AAPL",
        side=side,
        order_type=OrderType.LIMIT,
        quantity=quantity,
        price=price,
        timestamp_ns=order_id,
    )


def test_buy_order_reserves_cash():
    exchange = Exchange()

    buyer = exchange.create_account(
        account_id=1,
        initial_cash=10_000,
    )

    exchange.submit_order(
        make_request(
            order_id=1,
            account_id=1,
            side=Side.BUY,
            quantity=50,
            price=100,
        )
    )

    assert buyer.cash == 10_000
    assert buyer.reserved_cash == 5_000
    assert buyer.available_cash == 5_000


def test_buy_order_cannot_exceed_available_cash():
    exchange = Exchange()

    exchange.create_account(
        account_id=1,
        initial_cash=5_000,
    )

    exchange.submit_order(
        make_request(
            order_id=1,
            account_id=1,
            side=Side.BUY,
            quantity=50,
            price=100,
        )
    )

    with pytest.raises(
        ValueError,
        match="insufficient available cash",
    ):
        exchange.submit_order(
            make_request(
                order_id=2,
                account_id=1,
                side=Side.BUY,
                quantity=1,
                price=100,
            )
        )


def test_cancel_releases_reserved_cash():
    exchange = Exchange()

    buyer = exchange.create_account(
        account_id=1,
        initial_cash=10_000,
    )

    exchange.submit_order(
        make_request(
            order_id=1,
            account_id=1,
            side=Side.BUY,
            quantity=50,
            price=100,
        )
    )

    assert buyer.reserved_cash == 5_000

    assert exchange.cancel_order(
        "AAPL",
        1,
    )

    assert buyer.reserved_cash == 0
    assert buyer.available_cash == 10_000


def test_sell_order_reserves_inventory():
    exchange = Exchange()

    seller = exchange.create_account(
        account_id=1,
        initial_cash=10_000,
    )

    seller.update_position(
        "AAPL",
        100,
    )

    exchange.submit_order(
        make_request(
            order_id=1,
            account_id=1,
            side=Side.SELL,
            quantity=40,
            price=100,
        )
    )

    assert seller.get_position("AAPL") == 100
    assert seller.get_reserved_position("AAPL") == 40
    assert seller.get_available_position("AAPL") == 60


def test_sell_order_cannot_exceed_available_inventory():
    exchange = Exchange()

    seller = exchange.create_account(
        account_id=1,
        initial_cash=10_000,
    )

    seller.update_position(
        "AAPL",
        100,
    )

    exchange.submit_order(
        make_request(
            order_id=1,
            account_id=1,
            side=Side.SELL,
            quantity=80,
            price=100,
        )
    )

    with pytest.raises(
        ValueError,
        match="insufficient available position",
    ):
        exchange.submit_order(
            make_request(
                order_id=2,
                account_id=1,
                side=Side.SELL,
                quantity=21,
                price=100,
            )
        )


def test_cancel_releases_reserved_inventory():
    exchange = Exchange()

    seller = exchange.create_account(
        account_id=1,
        initial_cash=10_000,
    )

    seller.update_position(
        "AAPL",
        100,
    )

    exchange.submit_order(
        make_request(
            order_id=1,
            account_id=1,
            side=Side.SELL,
            quantity=40,
            price=100,
        )
    )

    assert seller.get_reserved_position("AAPL") == 40

    assert exchange.cancel_order(
        "AAPL",
        1,
    )

    assert seller.get_reserved_position("AAPL") == 0
    assert seller.get_available_position("AAPL") == 100


def test_filled_buy_releases_reserved_cash():
    exchange = Exchange()

    buyer = exchange.create_account(
        account_id=1,
        initial_cash=10_000,
    )

    seller = exchange.create_account(
        account_id=2,
        initial_cash=0,
    )

    seller.update_position(
        "AAPL",
        100,
    )

    exchange.submit_order(
        make_request(
            order_id=1,
            account_id=2,
            side=Side.SELL,
            quantity=50,
            price=100,
        )
    )

    exchange.submit_order(
        make_request(
            order_id=2,
            account_id=1,
            side=Side.BUY,
            quantity=50,
            price=100,
        )
    )

    assert buyer.cash == 5_000
    assert buyer.reserved_cash == 0
    assert buyer.available_cash == 5_000


def test_filled_sell_releases_reserved_inventory():
    exchange = Exchange()

    buyer = exchange.create_account(
        account_id=1,
        initial_cash=10_000,
    )

    seller = exchange.create_account(
        account_id=2,
        initial_cash=0,
    )

    seller.update_position(
        "AAPL",
        50,
    )

    exchange.submit_order(
        make_request(
            order_id=1,
            account_id=2,
            side=Side.SELL,
            quantity=50,
            price=100,
        )
    )

    exchange.submit_order(
        make_request(
            order_id=2,
            account_id=1,
            side=Side.BUY,
            quantity=50,
            price=100,
        )
    )

    assert seller.get_position("AAPL") == 0
    assert seller.get_reserved_position("AAPL") == 0
    assert seller.get_available_position("AAPL") == 0