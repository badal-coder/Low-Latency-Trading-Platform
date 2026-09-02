import time

from engine.matching_engine import MatchingEngine
from engine.order import Order, OrderType, Side


def make_order(order_id, side, price, quantity):
    return Order(
        order_id=order_id,
        symbol="BTCUSD",
        side=side,
        order_type=OrderType.LIMIT,
        price=price,
        quantity=quantity,
        timestamp_ns=order_id,
    )


def benchmark_order_submission(num_orders):
    engine = MatchingEngine()

    start = time.perf_counter_ns()

    for i in range(num_orders):
        order = make_order(
            order_id=i,
            side=Side.BUY,
            price=100,
            quantity=1,
        )

        engine.submit_order(order)

    elapsed_ns = time.perf_counter_ns() - start

    return elapsed_ns


def benchmark_cancellation(num_orders):
    engine = MatchingEngine()

    for i in range(num_orders):
        order = make_order(
            order_id=i,
            side=Side.BUY,
            price=100,
            quantity=1,
        )

        engine.submit_order(order)

    start = time.perf_counter_ns()

    for i in range(num_orders):
        engine.cancel_order("BTCUSD", i)

    elapsed_ns = time.perf_counter_ns() - start

    return elapsed_ns


def main():
    sizes = [
        1_000,
        10_000,
        100_000,
    ]

    print()
    print("LOW LATENCY EXCHANGE BENCHMARK")
    print("=" * 40)

    for size in sizes:
        elapsed = benchmark_order_submission(size)

        avg_ns = elapsed / size

        print(
            f"Submit {size:>7,} orders: "
            f"{elapsed / 1_000_000:.3f} ms total | "
            f"{avg_ns:.1f} ns/order"
        )

    print()

    for size in sizes:
        elapsed = benchmark_cancellation(size)

        avg_ns = elapsed / size

        print(
            f"Cancel {size:>7,} orders: "
            f"{elapsed / 1_000_000:.3f} ms total | "
            f"{avg_ns:.1f} ns/order"
        )


if __name__ == "__main__":
    main()