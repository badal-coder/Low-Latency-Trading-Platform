import pytest

from engine.account import Account
from engine.matching_engine import Trade
from engine.settlement import SettlementEngine


def make_trade(
    price=100,
    quantity=10,
):
    return Trade(
        trade_id=1,
        symbol="BTCUSD",
        price=price,
        quantity=quantity,
        buy_order_id=1,
        sell_order_id=2,
    )


def test_buy_settlement_updates_cash_and_position():
    buyer = Account(
        account_id=1,
        cash=5000,
    )

    seller = Account(
        account_id=2,
        cash=1000,
    )

    trade = make_trade(
        price=100,
        quantity=10,
    )

    SettlementEngine().settle(
        trade,
        buyer,
        seller,
    )

    assert buyer.cash == 4000
    assert buyer.get_position("BTCUSD") == 10

    assert seller.cash == 2000
    assert seller.get_position("BTCUSD") == -10


def test_settlement_uses_execution_price():
    buyer = Account(
        account_id=1,
        cash=10000,
    )

    seller = Account(
        account_id=2,
        cash=0,
    )

    trade = make_trade(
        price=250,
        quantity=4,
    )

    SettlementEngine().settle(
        trade,
        buyer,
        seller,
    )

    assert buyer.cash == 9000
    assert seller.cash == 1000


def test_partial_fill_settlement():
    buyer = Account(
        account_id=1,
        cash=10000,
    )

    seller = Account(
        account_id=2,
        cash=0,
    )

    trade = make_trade(
        price=100,
        quantity=3,
    )

    SettlementEngine().settle(
        trade,
        buyer,
        seller,
    )

    assert buyer.cash == 9700
    assert buyer.get_position("BTCUSD") == 3

    assert seller.cash == 300
    assert seller.get_position("BTCUSD") == -3


def test_multiple_trades_accumulate():
    buyer = Account(
        account_id=1,
        cash=10000,
    )

    seller = Account(
        account_id=2,
        cash=0,
    )

    settlement = SettlementEngine()

    settlement.settle(
        make_trade(price=100, quantity=5),
        buyer,
        seller,
    )

    settlement.settle(
        make_trade(price=200, quantity=2),
        buyer,
        seller,
    )

    assert buyer.cash == 9500 - 400
    assert buyer.get_position("BTCUSD") == 7

    assert seller.cash == 900
    assert seller.get_position("BTCUSD") == -7


def test_settlement_fails_if_buyer_has_insufficient_cash():
    buyer = Account(
        account_id=1,
        cash=500,
    )

    seller = Account(
        account_id=2,
        cash=0,
    )

    trade = make_trade(
        price=100,
        quantity=10,
    )

    with pytest.raises(ValueError, match="insufficient cash"):
        SettlementEngine().settle(
            trade,
            buyer,
            seller,
        )

    assert buyer.cash == 500
    assert buyer.get_position("BTCUSD") == 0

    assert seller.cash == 0
    assert seller.get_position("BTCUSD") == 0