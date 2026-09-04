import statistics
import time

from engine.matching_engine import MatchingEngine
from engine.order import Order, OrderType, Side


SYMBOL = "AAPL"
PRICE = 100
QUANTITY = 1


def make_order(
    order_id: int,
    side: Side,
    timestamp_ns: int,
) -> Order:
    return Order(
        order_id=order_id,
        account_id=1,
        symbol=SYMBOL,
        side=side,
        order_type=OrderType.LIMIT,
        price=PRICE,
        quantity=QUANTITY,
        timestamp_ns=timestamp_ns,
    )


def percentile(values, p):
    values = sorted(values)

    index = (len(values) - 1) * p

    lower = int(index)
    upper = min(lower + 1, len(values) - 1)

    if lower == upper:
        return values[lower]

    fraction = index - lower

    return (
        values[lower]
        + (values[upper] - values[lower]) * fraction
    )


def run_scaling_benchmark(iterations: int):
    """
    Benchmark matching-engine performance at different workloads.

    Each iteration submits:

        SELL -> BUY -> 1 trade

    Therefore:

        orders = iterations * 2
        trades = iterations
    """

    engine = MatchingEngine()

    latencies = []
    trades = 0

    start = time.perf_counter_ns()

    for i in range(iterations):

        sell_id = (i * 2) + 1
        buy_id = (i * 2) + 2

        sell = make_order(
            sell_id,
            Side.SELL,
            sell_id,
        )

        buy = make_order(
            buy_id,
            Side.BUY,
            buy_id,
        )

        order_start = time.perf_counter_ns()

        trades += len(
            engine.submit_order(sell)
        )

        trades += len(
            engine.submit_order(buy)
        )

        order_end = time.perf_counter_ns()

        # Two orders processed.
        latencies.append(
            (order_end - order_start) / 2
        )

    elapsed_ns = (
        time.perf_counter_ns() - start
    )

    orders = iterations * 2

    throughput = (
        orders
        / (elapsed_ns / 1_000_000_000)
    )

    return {
        "iterations": iterations,
        "orders": orders,
        "trades": trades,
        "throughput": throughput,
        "min_latency": min(latencies),
        "median_latency": statistics.median(latencies),
        "p95_latency": percentile(latencies, 0.95),
        "p99_latency": percentile(latencies, 0.99),
        "max_latency": max(latencies),
    }


def test_matching_engine_scaling_benchmark():

    # ---------------------------------------------------------
    # Warm-up
    # ---------------------------------------------------------

    run_scaling_benchmark(1_000)

    # ---------------------------------------------------------
    # Workloads
    # ---------------------------------------------------------

    workloads = [
        5_000,
        12_500,
        25_000,
        50_000,
    ]

    results = []

    for iterations in workloads:

        result = run_scaling_benchmark(
            iterations
        )

        results.append(result)

    # ---------------------------------------------------------
    # Report
    # ---------------------------------------------------------

    print()
    print("========== MATCHING ENGINE SCALING ==========")

    print()
    print(
        f"{'Orders':>10} "
        f"{'Trades':>10} "
        f"{'Throughput':>16} "
        f"{'Median':>12} "
        f"{'p95':>12} "
        f"{'p99':>12}"
    )

    print("-" * 78)

    for result in results:

        print(
            f"{result['orders']:>10,} "
            f"{result['trades']:>10,} "
            f"{result['throughput']:>13,.0f}/s "
            f"{result['median_latency']:>9,.0f} ns "
            f"{result['p95_latency']:>9,.0f} ns "
            f"{result['p99_latency']:>9,.0f} ns"
        )

    print()
    print("==============================================")

    # ---------------------------------------------------------
    # Correctness
    # ---------------------------------------------------------

    for result in results:

        expected_orders = (
            result["iterations"] * 2
        )

        expected_trades = (
            result["iterations"]
        )

        assert result["orders"] == expected_orders

        assert result["trades"] == expected_trades