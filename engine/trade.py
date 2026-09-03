from dataclasses import dataclass


@dataclass(slots=True)
class Trade:
    trade_id: int
    symbol: str
    price: int
    quantity: int
    buy_order_id: int
    sell_order_id: int
    