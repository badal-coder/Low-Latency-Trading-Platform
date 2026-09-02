import gc
import statistics
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


def percentile(values, percentile):
    values = sorted(values)

    index = int((percentile / 100) * (len(values) - 1))

    return values[index]


def benchmark_submission(iterations=10_000):
    engine = MatchingEngine()

    latencies = []

    gc.disable()

    try:
        for i in range(iterations):
            order = make_order(
                order_id=i,
                side=Side.BUY,
                price=100 + (i % 10),
                quantity=1,
            )

            start = time.perf_counter_ns()

            engine.submit_order(order)

            end = time.perf_counter_ns()

            latencies.append(end - start)

    finally:
        gc.enable()

    return latencies


def benchmark_cancellation(iterations=10_000):
    engine = MatchingEngine()

    for i in range(iterations):
        order = make_order(
            order_id=i,
            side=Side.BUY,
            price=100,
            quantity=1,
        )

        engine.submit_order(order)

    latencies = []

    gc.disable()

    try:
        for i in range(iterations):
            start = time.perf_counter_ns()

            engine.cancel_order("BTCUSD", i)

            end = time.perf_counter_ns()

            latencies.append(end - start)

    finally:
        gc.enable()

    return latencies


def print_results(name, latencies):
    print()
    print(name)
    print("-" * 50)

    print(f"Samples : {len(latencies):,}")
    print(f"Mean    : {statistics.mean(latencies):,.1f} ns")
    print(f"Median  : {statistics.median(latencies):,.1f} ns")
    print(f"p50     : {percentile(latencies, 50):,.1f} ns")
    print(f"p95     : {percentile(latencies, 95):,.1f} ns")
    print(f"p99     : {percentile(latencies, 99):,.1f} ns")
    print(f"p99.9   : {percentile(latencies, 99.9):,.1f} ns")
    print(f"Min     : {min(latencies):,.1f} ns")
    print(f"Max     : {max(latencies):,.1f} ns")


def main():
    print()
    print("LOW LATENCY EXCHANGE")
    print("=====================")

    submission = benchmark_submission()

    print_results(
        "ORDER SUBMISSION LATENCY",
        submission,
    )

    cancellation = benchmark_cancellation()

    print_results(
        "ORDER CANCELLATION LATENCY",
        cancellation,
    )


if __name__ == "__main__":
    main()