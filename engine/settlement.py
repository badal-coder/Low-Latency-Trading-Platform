from .account import Account
from .trade import Trade


class SettlementEngine:

    def settle(
        self,
        trade: Trade,
        buyer: Account,
        seller: Account,
    ) -> None:

        notional = trade.price * trade.quantity

        # Buyer pays cash and receives the asset.
        buyer.withdraw(notional)
        buyer.update_position(
            trade.symbol,
            trade.quantity,
        )

        # Seller receives cash and gives up the asset.
        seller.deposit(notional)
        seller.update_position(
            trade.symbol,
            -trade.quantity,
        )