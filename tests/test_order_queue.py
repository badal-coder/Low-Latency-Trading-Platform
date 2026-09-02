from engine.order import Order, OrderType, Side
from engine.order_queue import OrderQueue


def make_order(order_id):
    return Order(
        order_id=order_id,
        symbol="BTCUSD",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        price=100,
        quantity=10,
        timestamp_ns=order_id,
    )


def test_append_and_peek():
    queue = OrderQueue()

    order1 = make_order(1)
    order2 = make_order(2)

    node1 = queue.append(order1)
    queue.append(order2)

    assert queue.peek() is node1
    assert queue.peek().order.order_id == 1
    assert len(queue) == 2


def test_fifo_order():
    queue = OrderQueue()

    queue.append(make_order(1))
    queue.append(make_order(2))
    queue.append(make_order(3))

    assert queue.popleft().order.order_id == 1
    assert queue.popleft().order.order_id == 2
    assert queue.popleft().order.order_id == 3
    assert queue.popleft() is None


def test_remove_middle():
    queue = OrderQueue()

    node1 = queue.append(make_order(1))
    node2 = queue.append(make_order(2))
    node3 = queue.append(make_order(3))

    queue.remove(node2)

    assert queue.peek() is node1
    assert node1.next is node3
    assert node3.prev is node1
    assert len(queue) == 2


def test_remove_head():
    queue = OrderQueue()

    node1 = queue.append(make_order(1))
    node2 = queue.append(make_order(2))

    queue.remove(node1)

    assert queue.head is node2
    assert node2.prev is None
    assert queue.tail is node2


def test_remove_tail():
    queue = OrderQueue()

    node1 = queue.append(make_order(1))
    node2 = queue.append(make_order(2))

    queue.remove(node2)

    assert queue.tail is node1
    assert node1.next is None
    assert queue.head is node1


def test_remove_only_node():
    queue = OrderQueue()

    node = queue.append(make_order(1))

    queue.remove(node)

    assert queue.head is None
    assert queue.tail is None
    assert len(queue) == 0
    