import pytest

from engine.order import (
    Order,
    OrderStatus,
    OrderType,
    Side,
)


def make_order(
    quantity: int = 100,
) -> Order:
    return Order(
        order_id=1,
        symbol="BTCUSD",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        price=100,
        quantity=quantity,
        timestamp_ns=1,
    )


def test_new_order_starts_open():
    order = make_order()

    assert order.status == OrderStatus.OPEN
    assert order.filled_quantity == 0
    assert order.remaining_quantity == 100
    assert order.is_active is True
    assert order.is_terminal is False


def test_partial_fill_changes_status():
    order = make_order()

    order.fill(40)

    assert order.status == OrderStatus.PARTIALLY_FILLED
    assert order.filled_quantity == 40
    assert order.remaining_quantity == 60
    assert order.is_active is True


def test_full_fill_changes_status():
    order = make_order()

    order.fill(100)

    assert order.status == OrderStatus.FILLED
    assert order.filled_quantity == 100
    assert order.remaining_quantity == 0
    assert order.is_active is False
    assert order.is_terminal is True


def test_partial_then_full_fill():
    order = make_order()

    order.fill(40)
    order.fill(60)

    assert order.status == OrderStatus.FILLED
    assert order.filled_quantity == 100
    assert order.remaining_quantity == 0


def test_open_order_can_be_cancelled():
    order = make_order()

    order.cancel()

    assert order.status == OrderStatus.CANCELLED
    assert order.is_active is False
    assert order.is_terminal is True


def test_partially_filled_order_can_be_cancelled():
    order = make_order()

    order.fill(40)
    order.cancel()

    assert order.status == OrderStatus.CANCELLED
    assert order.filled_quantity == 40
    assert order.remaining_quantity == 60


def test_filled_order_cannot_be_cancelled():
    order = make_order()

    order.fill(100)
    order.cancel()

    assert order.status == OrderStatus.FILLED


def test_cancelled_order_remains_cancelled():
    order = make_order()

    order.cancel()
    order.cancel()

    assert order.status == OrderStatus.CANCELLED


def test_cannot_fill_cancelled_order():
    order = make_order()

    order.cancel()

    with pytest.raises(
        ValueError,
        match="cannot fill terminal order",
    ):
        order.fill(10)


def test_cannot_fill_filled_order():
    order = make_order()

    order.fill(100)

    with pytest.raises(
        ValueError,
        match="cannot fill terminal order",
    ):
        order.fill(1)


def test_cannot_overfill_order():
    order = make_order()

    order.fill(90)

    with pytest.raises(
        ValueError,
        match="fill quantity exceeds remaining quantity",
    ):
        order.fill(11)


def test_zero_fill_is_rejected():
    order = make_order()

    with pytest.raises(
        ValueError,
        match="fill quantity must be positive",
    ):
        order.fill(0)


def test_negative_fill_is_rejected():
    order = make_order()

    with pytest.raises(
        ValueError,
        match="fill quantity must be positive",
    ):
        order.fill(-1)


def test_reject_order():
    order = make_order()

    order.reject()

    assert order.status == OrderStatus.REJECTED
    assert order.is_active is False
    assert order.is_terminal is True


def test_rejected_order_cannot_be_filled():
    order = make_order()

    order.reject()

    with pytest.raises(
        ValueError,
        match="cannot fill terminal order",
    ):
        order.fill(10)