import pytest

from engine.account import Account


def test_account_starts_with_cash():
    account = Account(
        account_id=1,
        cash=100_000,
    )

    assert account.cash == 100_000
    assert account.positions == {}


def test_deposit_increases_cash():
    account = Account(
        account_id=1,
        cash=100_000,
    )

    account.deposit(50_000)

    assert account.cash == 150_000


def test_withdraw_decreases_cash():
    account = Account(
        account_id=1,
        cash=100_000,
    )

    account.withdraw(25_000)

    assert account.cash == 75_000


def test_cannot_withdraw_more_than_cash():
    account = Account(
        account_id=1,
        cash=100_000,
    )

    with pytest.raises(ValueError):
        account.withdraw(100_001)

    assert account.cash == 100_000


def test_cannot_deposit_zero():
    account = Account(
        account_id=1,
        cash=100_000,
    )

    with pytest.raises(ValueError):
        account.deposit(0)


def test_position_starts_at_zero():
    account = Account(
        account_id=1,
        cash=100_000,
    )

    assert account.get_position("BTCUSD") == 0


def test_buy_updates_position():
    account = Account(
        account_id=1,
        cash=100_000,
    )

    account.update_position("BTCUSD", 50)

    assert account.get_position("BTCUSD") == 50


def test_sell_updates_position():
    account = Account(
        account_id=1,
        cash=100_000,
    )

    account.update_position("BTCUSD", 50)
    account.update_position("BTCUSD", -20)

    assert account.get_position("BTCUSD") == 30


def test_zero_position_is_removed():
    account = Account(
        account_id=1,
        cash=100_000,
    )

    account.update_position("BTCUSD", 50)
    account.update_position("BTCUSD", -50)

    assert account.get_position("BTCUSD") == 0
    assert "BTCUSD" not in account.positions