from .account import Account


class AccountManager:
    """
    Manages accounts registered with the exchange.

    Responsible for:
    - creating accounts
    - looking up accounts
    - preventing duplicate account IDs
    """

    def __init__(self):
        self.accounts: dict[int, Account] = {}

    def create_account(
        self,
        account_id: int,
        initial_cash: int = 0,
    ) -> Account:

        if account_id in self.accounts:
            raise ValueError("account already exists")

        if initial_cash < 0:
            raise ValueError("initial cash cannot be negative")

        account = Account(
            account_id=account_id,
            cash=initial_cash,
        )

        self.accounts[account_id] = account

        return account

    def get_account(
        self,
        account_id: int,
    ) -> Account:

        account = self.accounts.get(account_id)

        if account is None:
            raise ValueError("account does not exist")

        return account

    def has_account(
        self,
        account_id: int,
    ) -> bool:

        return account_id in self.accounts

    def deposit(
        self,
        account_id: int,
        amount: int,
    ) -> None:

        account = self.get_account(account_id)
        account.deposit(amount)

    def withdraw(
        self,
        account_id: int,
        amount: int,
    ) -> None:

        account = self.get_account(account_id)
        account.withdraw(amount)