from engine.order import Order, OrderType, Side
from engine.order_book import OrderBook


def test_order_book():
    book = OrderBook("BTCUSD")

    buy1 = Order(
        order_id=1,
        symbol="BTCUSD",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        price=100,
        quantity=10,
        timestamp_ns=1,
    )

    buy2 = Order(
        order_id=2,
        symbol="BTCUSD",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        price=101,
        quantity=5,
        timestamp_ns=2,
    )

    book.add_order(buy1)
    book.add_order(buy2)

    assert book.best_bid() == 101