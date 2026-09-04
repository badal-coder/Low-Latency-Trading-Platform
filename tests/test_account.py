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
def test_available_cash_excludes_reserved_cash():
    account = Account(
        account_id=1,
        cash=10_000,
    )

    account.reserve_cash(3_000)

    assert account.cash == 10_000
    assert account.reserved_cash == 3_000
    assert account.available_cash == 7_000


def test_reserve_cash():
    account = Account(
        account_id=1,
        cash=10_000,
    )

    account.reserve_cash(4_000)

    assert account.reserved_cash == 4_000
    assert account.available_cash == 6_000


def test_cannot_reserve_more_than_available_cash():
    account = Account(
        account_id=1,
        cash=10_000,
    )

    with pytest.raises(ValueError, match="insufficient available cash"):
        account.reserve_cash(10_001)


def test_release_cash():
    account = Account(
        account_id=1,
        cash=10_000,
    )

    account.reserve_cash(4_000)
    account.release_cash(1_500)

    assert account.reserved_cash == 2_500
    assert account.available_cash == 7_500


def test_cannot_release_more_than_reserved():
    account = Account(
        account_id=1,
        cash=10_000,
    )

    account.reserve_cash(2_000)

    with pytest.raises(
        ValueError,
        match="cannot release more than reserved cash",
    ):
        account.release_cash(3_000)