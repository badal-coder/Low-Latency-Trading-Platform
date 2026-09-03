import pytest

from engine.account_manager import AccountManager


def test_create_account():

    manager = AccountManager()

    account = manager.create_account(
        account_id=100,
        initial_cash=10_000,
    )

    assert account.account_id == 100
    assert account.cash == 10_000


def test_account_can_be_retrieved():

    manager = AccountManager()

    manager.create_account(
        account_id=100,
        initial_cash=10_000,
    )

    account = manager.get_account(100)

    assert account.account_id == 100


def test_unknown_account_fails():

    manager = AccountManager()

    with pytest.raises(ValueError, match="account does not exist"):
        manager.get_account(999)


def test_duplicate_account_fails():

    manager = AccountManager()

    manager.create_account(
        account_id=100,
        initial_cash=10_000,
    )

    with pytest.raises(ValueError, match="account already exists"):
        manager.create_account(
            account_id=100,
            initial_cash=5_000,
        )


def test_negative_initial_cash_fails():

    manager = AccountManager()

    with pytest.raises(
        ValueError,
        match="initial cash cannot be negative",
    ):
        manager.create_account(
            account_id=100,
            initial_cash=-1,
        )


def test_deposit():

    manager = AccountManager()

    manager.create_account(
        account_id=100,
        initial_cash=1_000,
    )

    manager.deposit(
        account_id=100,
        amount=500,
    )

    assert manager.get_account(100).cash == 1_500


def test_withdraw():

    manager = AccountManager()

    manager.create_account(
        account_id=100,
        initial_cash=1_000,
    )

    manager.withdraw(
        account_id=100,
        amount=400,
    )

    assert manager.get_account(100).cash == 600


def test_has_account():

    manager = AccountManager()

    assert manager.has_account(100) is False

    manager.create_account(
        account_id=100,
        initial_cash=1_000,
    )

    assert manager.has_account(100) is True