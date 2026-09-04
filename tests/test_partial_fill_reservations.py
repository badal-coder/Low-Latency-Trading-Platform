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
    symbol="AAPL",
):
    return OrderRequest(
        order_id=order_id,
        account_id=account_id,
        symbol=symbol,
        side=side,
        order_type=OrderType.LIMIT,
        quantity=quantity,
        price=price,
        timestamp_ns=order_id,
    )


def test_buy_partial_fill_keeps_only_remaining_cash_reserved():

    exchange = Exchange()

    buyer = exchange.create_account(
        account_id=1,
        initial_cash=10_000,
    )

    seller = exchange.create_account(
        account_id=2,
        initial_cash=0,
    )

    seller.update_position("AAPL", 5)

    exchange.submit_order(
        make_request(
            order_id=1,
            account_id=1,
            side=Side.BUY,
            quantity=10,
            price=100,
        )
    )

    exchange.submit_order(
        make_request(
            order_id=2,
            account_id=2,
            side=Side.SELL,
            quantity=5,
            price=100,
        )
    )

    assert buyer.cash == 9_500
    assert buyer.reserved_cash == 500


def test_sell_partial_fill_keeps_only_remaining_inventory_reserved():

    exchange = Exchange()

    buyer = exchange.create_account(
        account_id=1,
        initial_cash=10_000,
    )

    seller = exchange.create_account(
        account_id=2,
        initial_cash=0,
    )

    seller.update_position("AAPL", 10)

    exchange.submit_order(
        make_request(
            order_id=1,
            account_id=2,
            side=Side.SELL,
            quantity=10,
            price=100,
        )
    )

    exchange.submit_order(
        make_request(
            order_id=2,
            account_id=1,
            side=Side.BUY,
            quantity=5,
            price=100,
        )
    )

    assert seller.get_position("AAPL") == 5
    assert seller.get_reserved_position("AAPL") == 5


def test_cancel_partially_filled_buy_releases_remaining_cash():

    exchange = Exchange()

    buyer = exchange.create_account(
        account_id=1,
        initial_cash=10_000,
    )

    seller = exchange.create_account(
        account_id=2,
        initial_cash=0,
    )

    seller.update_position("AAPL", 5)

    exchange.submit_order(
        make_request(
            order_id=1,
            account_id=1,
            side=Side.BUY,
            quantity=10,
            price=100,
        )
    )

    exchange.submit_order(
        make_request(
            order_id=2,
            account_id=2,
            side=Side.SELL,
            quantity=5,
            price=100,
        )
    )

    assert buyer.reserved_cash == 500

    assert exchange.cancel_order(
        "AAPL",
        1,
    )

    assert buyer.cash == 9_500
    assert buyer.reserved_cash == 0


def test_cancel_partially_filled_sell_releases_remaining_inventory():

    exchange = Exchange()

    buyer = exchange.create_account(
        account_id=1,
        initial_cash=10_000,
    )

    seller = exchange.create_account(
        account_id=2,
        initial_cash=0,
    )

    seller.update_position("AAPL", 10)

    exchange.submit_order(
        make_request(
            order_id=1,
            account_id=2,
            side=Side.SELL,
            quantity=10,
            price=100,
        )
    )

    exchange.submit_order(
        make_request(
            order_id=2,
            account_id=1,
            side=Side.BUY,
            quantity=5,
            price=100,
        )
    )

    assert seller.get_reserved_position("AAPL") == 5

    assert exchange.cancel_order(
        "AAPL",
        1,
    )

    assert seller.get_position("AAPL") == 5
    assert seller.get_reserved_position("AAPL") == 0