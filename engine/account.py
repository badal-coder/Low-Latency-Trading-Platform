from dataclasses import dataclass, field


@dataclass(slots=True)
class Account:
    account_id: int
    cash: int

    positions: dict[str, int] = field(default_factory=dict)

    def get_position(self, symbol: str) -> int:
        return self.positions.get(symbol, 0)

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