from engine.order import Order, OrderType, Side
from engine.order_book import OrderBook


def make_order(
    order_id: int,
    side: Side,
    price: int,
    quantity: int = 10,
    timestamp_ns: int = 1,
):
    return Order(
        order_id=order_id,
        symbol="BTCUSD",
        side=side,
        order_type=OrderType.LIMIT,
        price=price,
        quantity=quantity,
        timestamp_ns=timestamp_ns,
    )


def test_best_bid_returns_highest_buy_price():
    book = OrderBook("BTCUSD")

    book.add_order(
        make_order(1, Side.BUY, 100)
    )

    book.add_order(
        make_order(2, Side.BUY, 101)
    )

    book.add_order(
        make_order(3, Side.BUY, 99)
    )

    assert book.best_bid() == 101


def test_best_ask_returns_lowest_sell_price():
    book = OrderBook("BTCUSD")

    book.add_order(
        make_order(1, Side.SELL, 105)
    )

    book.add_order(
        make_order(2, Side.SELL, 103)
    )

    book.add_order(
        make_order(3, Side.SELL, 110)
    )

    assert book.best_ask() == 103


def test_empty_book_has_no_best_prices():
    book = OrderBook("BTCUSD")

    assert book.best_bid() is None
    assert book.best_ask() is None


def test_order_is_stored_by_id():
    book = OrderBook("BTCUSD")

    order = make_order(
        1,
        Side.BUY,
        100,
    )

    book.add_order(order)

    assert book.orders[1] is order


def test_cancel_removes_order():
    book = OrderBook("BTCUSD")

    order = make_order(
        1,
        Side.BUY,
        100,
    )

    book.add_order(order)

    assert book.remove_order(1) is True

    assert 1 not in book.orders
    assert book.best_bid() is None


def test_cancel_middle_order_preserves_other_orders():
    book = OrderBook("BTCUSD")

    order1 = make_order(1, Side.BUY, 100)
    order2 = make_order(2, Side.BUY, 100)
    order3 = make_order(3, Side.BUY, 100)

    book.add_order(order1)
    book.add_order(order2)
    book.add_order(order3)

    assert book.remove_order(2) is True

    assert 1 in book.orders
    assert 2 not in book.orders
    assert 3 in book.orders


def test_fifo_order_is_preserved():
    book = OrderBook("BTCUSD")

    order1 = make_order(
        1,
        Side.BUY,
        100,
        timestamp_ns=1,
    )

    order2 = make_order(
        2,
        Side.BUY,
        100,
        timestamp_ns=2,
    )

    book.add_order(order1)
    book.add_order(order2)

    node = book.bids[100].orders.peek()

    assert node is not None
    assert node.order.order_id == 1


def test_filled_order_is_removed():
    book = OrderBook("BTCUSD")

    order = make_order(
        1,
        Side.BUY,
        100,
    )

    book.add_order(order)

    level = book.bids[100]

    book.remove_filled_order(
        level,
        order,
    )

    assert 1 not in book.orders
    assert 1 not in book.order_nodes
    assert book.best_bid() is None