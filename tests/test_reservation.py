import pytest
from engine.account import Account
from engine.reservation import (
    CashReservation,
    PositionReservation,
    ReservationEngine,
)
def test_reserve_cash():
    account = Account(
        account_id=1,
        cash=10_000,
    )
    reservation = ReservationEngine().reserve_cash(
        account,
        3_000,
    )
    assert isinstance(reservation, CashReservation)
    assert reservation.account_id == 1
    assert reservation.amount == 3_000
    assert account.cash == 10_000
    assert account.reserved_cash == 3_000
    assert account.available_cash == 7_000
def test_cannot_reserve_more_cash_than_available():
    account = Account(
        account_id=1,
        cash=10_000,
    )
    account.reserve_cash(7_000)
    with pytest.raises(
        ValueError,
        match="insufficient available cash",
    ):
        account.reserve_cash(4_000)
def test_release_cash():
    account = Account(
        account_id=1,
        cash=10_000,
    )
    reservation_engine = ReservationEngine()
    reservation = reservation_engine.reserve_cash(
        account,
        3_000,
    )
    reservation_engine.release_cash(
        account,
        reservation,
    )
    assert account.cash == 10_000
    assert account.reserved_cash == 0
    assert account.available_cash == 10_000
def test_reserve_position():
    account = Account(
        account_id=1,
        cash=10_000,
    )
    account.update_position(
        "AAPL",
        100,
    )
    reservation = ReservationEngine().reserve_position(
        account,
        "AAPL",
        40,
    )
    assert isinstance(reservation, PositionReservation)
    assert reservation.account_id == 1
    assert reservation.symbol == "AAPL"
    assert reservation.quantity == 40
    assert account.get_position("AAPL") == 100
    assert account.get_reserved_position("AAPL") == 40
    assert account.get_available_position("AAPL") == 60
def test_cannot_reserve_more_position_than_available():
    account = Account(
        account_id=1,
        cash=10_000,
    )
    account.update_position(
        "AAPL",
        100,
    )
    account.reserve_position(
        "AAPL",
        70,
    )
    with pytest.raises(
        ValueError,
        match="insufficient available position",
    ):
        account.reserve_position(
            "AAPL",
            31,
        )
def test_release_position():
    account = Account(
        account_id=1,
        cash=10_000,
    )
    account.update_position(
        "AAPL",
        100,
    )
    reservation_engine = ReservationEngine()
    reservation = reservation_engine.reserve_position(
        account,
        "AAPL",
        40,
    )
    reservation_engine.release_position(
        account,
        reservation,
    )
    assert account.get_position("AAPL") == 100
    assert account.get_reserved_position("AAPL") == 0
    assert account.get_available_position("AAPL") == 100
def test_multiple_cash_reservations():
    account = Account(
        account_id=1,
        cash=10_000,
    )
    account.reserve_cash(3_000)
    account.reserve_cash(2_000)
    assert account.reserved_cash == 5_000
    assert account.available_cash == 5_000
def test_multiple_position_reservations():
    account = Account(
        account_id=1,
        cash=10_000,
    )
    account.update_position(
        "AAPL",
        100,
    )
    account.reserve_position(
        "AAPL",
        30,
    )
    account.reserve_position(
        "AAPL",
        20,
    )
    assert account.get_reserved_position("AAPL") == 50
    assert account.get_available_position("AAPL") == 50
