from dataclasses import dataclass, field


@dataclass(slots=True)
class Account:
    account_id: int
    cash: int

    positions: dict[str, int] = field(default_factory=dict)

    # Resources reserved by open orders.
    reserved_cash: int = 0
    reserved_positions: dict[str, int] = field(
        default_factory=dict
    )

    @property
    def available_cash(self) -> int:
        return self.cash - self.reserved_cash

    def get_position(self, symbol: str) -> int:
        return self.positions.get(symbol, 0)

    def get_reserved_position(self, symbol: str) -> int:
        return self.reserved_positions.get(symbol, 0)

    def get_available_position(self, symbol: str) -> int:
        return (
            self.get_position(symbol)
            - self.get_reserved_position(symbol)
        )

    def deposit(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("deposit amount must be positive")

        self.cash += amount

    def withdraw(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("withdraw amount must be positive")

        if amount > self.cash:
            raise ValueError("insufficient cash")

        self.cash -= amount

    def reserve_cash(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError(
                "reserve amount must be positive"
            )

        if amount > self.available_cash:
            raise ValueError(
                "insufficient available cash"
            )

        self.reserved_cash += amount

    def release_cash(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError(
                "release amount must be positive"
            )

        if amount > self.reserved_cash:
            raise ValueError(
                "cannot release more than reserved cash"
            )

        self.reserved_cash -= amount

    def reserve_position(
        self,
        symbol: str,
        quantity: int,
    ) -> None:
        if quantity <= 0:
            raise ValueError(
                "reserve quantity must be positive"
            )

        if quantity > self.get_available_position(symbol):
            raise ValueError(
                "insufficient available position"
            )

        self.reserved_positions[symbol] = (
            self.get_reserved_position(symbol)
            + quantity
        )

    def release_position(
        self,
        symbol: str,
        quantity: int,
    ) -> None:
        if quantity <= 0:
            raise ValueError(
                "release quantity must be positive"
            )

        reserved = self.get_reserved_position(symbol)

        if quantity > reserved:
            raise ValueError(
                "cannot release more reserved position"
            )

        remaining = reserved - quantity

        if remaining == 0:
            del self.reserved_positions[symbol]
        else:
            self.reserved_positions[symbol] = remaining

    def update_position(
        self,
        symbol: str,
        quantity: int,
    ) -> None:
        self.positions[symbol] = (
            self.get_position(symbol) + quantity
        )

        if self.positions[symbol] == 0:
            del self.positions[symbol]