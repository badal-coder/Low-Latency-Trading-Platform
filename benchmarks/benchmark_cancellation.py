import time

from engine.order import Order, OrderType, Side
from engine.order_queue import OrderQueue


def make_order(order_id):
    return Order(
        order_id=order_id,
        symbol="BTCUSD",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        price=100,
        quantity=1,
        timestamp_ns=order_id,
    )


def benchmark_direct_removal(size, repetitions=100):
    total_ns = 0

    for _ in range(repetitions):
        queue = OrderQueue()

        nodes = [
            queue.append(make_order(i))
            for i in range(size)
        ]

        middle = nodes[size // 2]

        start = time.perf_counter_ns()

        queue.remove(middle)

        total_ns += time.perf_counter_ns() - start

    return total_ns / repetitions


def benchmark_pop_left(size, repetitions=100):
    total_ns = 0

    for _ in range(repetitions):
        queue = OrderQueue()

        for i in range(size):
            queue.append(make_order(i))

        start = time.perf_counter_ns()

        queue.popleft()

        total_ns += time.perf_counter_ns() - start

    return total_ns / repetitions


def main():
    sizes = [
        1_000,
        10_000,
        100_000,
        500_000,
    ]

    print()
    print("ORDER QUEUE COMPLEXITY BENCHMARK")
    print("=" * 45)

    print()
    print("Direct middle-node removal")
    print("-" * 45)

    for size in sizes:
        elapsed = benchmark_direct_removal(size)

        print(
            f"{size:>8,} nodes: "
            f"{elapsed:.1f} ns"
        )

    print()
    print("FIFO popleft")
    print("-" * 45)

    for size in sizes:
        elapsed = benchmark_pop_left(size)

        print(
            f"{size:>8,} nodes: "
            f"{elapsed:.1f} ns"
        )


if __name__ == "__main__":
    main()