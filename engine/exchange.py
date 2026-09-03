from .account import Account
from .account_manager import AccountManager
from .gateway import Gateway, OrderGateway, OrderRequest
from .matching_engine import MatchingEngine, Trade
from .settlement import SettlementEngine


class Exchange:
    def __init__(self):
        self.matching_engine = MatchingEngine()

        self.gateway = OrderGateway(
            self.matching_engine
        )

        # Compatibility with code that imports/uses Gateway.
        self.order_gateway = self.gateway

        self.accounts = AccountManager()

        self.settlement = SettlementEngine()

    def create_account(
        self,
        account_id: int,
        initial_cash: int,
    ) -> Account:

        return self.accounts.create_account(
            account_id,
            initial_cash,
        )

    def submit_order(
        self,
        request: OrderRequest,
    ) -> list[Trade]:

        # Make sure the account exists before submitting.
        account = self.accounts.get_account(
            request.account_id
        )

        trades = self.gateway.submit(request)

        # Settle every execution immediately.
        for trade in trades:
            self._settle_trade(trade)

        return trades

    def cancel_order(
        self,
        symbol: str,
        order_id: int,
    ) -> bool:

        return self.gateway.cancel(
            symbol,
            order_id,
        )

    def _settle_trade(
        self,
        trade: Trade,
    ) -> None:

        buyer_order = self._find_order(
            trade.symbol,
            trade.buy_order_id,
        )

        seller_order = self._find_order(
            trade.symbol,
            trade.sell_order_id,
        )

        buyer = self.accounts.get_account(
            buyer_order.account_id
        )

        seller = self.accounts.get_account(
            seller_order.account_id
        )

        self.settlement.settle(
            trade,
            buyer,
            seller,
        )

    def _find_order(
        self,
        symbol: str,
        order_id: int,
    ):
        # First check the gateway's persistent order store.
        order = self.gateway.orders.get(order_id)

        if order is not None:
            return order

        # Fall back to the live order book.
        book = self.matching_engine.get_book(symbol)

        order = book.orders.get(order_id)

        if order is not None:
            return order

        raise ValueError(
            f"order {order_id} is no longer available"
        )