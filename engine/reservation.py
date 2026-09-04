from dataclasses import dataclass

from .account import Account


@dataclass(slots=True)
class CashReservation:
    account_id: int
    amount: int


@dataclass(slots=True)
class PositionReservation:
    account_id: int
    symbol: str
    quantity: int


class ReservationEngine:
    """
    Manages funds and inventory reserved for open orders.

    Reservations prevent multiple resting orders from
    consuming the same buying power or inventory.
    """

    def reserve_cash(
        self,
        account: Account,
        amount: int,
    ) -> CashReservation:

        account.reserve_cash(amount)

        return CashReservation(
            account_id=account.account_id,
            amount=amount,
        )

    def release_cash(
        self,
        account: Account,
        reservation: CashReservation,
    ) -> None:

        account.release_cash(
            reservation.amount
        )

    def reserve_position(
        self,
        account: Account,
        symbol: str,
        quantity: int,
    ) -> PositionReservation:

        account.reserve_position(
            symbol,
            quantity,
        )

        return PositionReservation(
            account_id=account.account_id,
            symbol=symbol,
            quantity=quantity,
        )

    def release_position(
        self,
        account: Account,
        reservation: PositionReservation,
    ) -> None:

        account.release_position(
            reservation.symbol,
            reservation.quantity,
        )