import time
from statistics import mean, median

from engine.matching_engine import MatchingEngine
from engine.order import Order, OrderType, Side


def make_order(
    order_id: int,
    side: Side,
    price: int,
    quantity: int,
    timestamp_ns: int,
) -> Order:
    return Order(
        order_id=order_id,
        account_id=1,
        symbol="AAPL",
        side=side,
        order_type=OrderType.LIMIT,
        price=price,
        quantity=quantity,
        timestamp_ns=timestamp_ns,
    )


def run_benchmark(iterations: int = 50_000):
    engine = MatchingEngine()

    start = time.perf_counter_ns()

    trades = 0

    for i in range(iterations):
        sell = make_order(
            order_id=(i * 2) + 1,
            side=Side.SELL,
            price=100,
            quantity=1,
            timestamp_ns=(i * 2) + 1,
        )

        buy = make_order(
            order_id=(i * 2) + 2,
            side=Side.BUY,
            price=100,
            quantity=1,
            timestamp_ns=(i * 2) + 2,
        )

        trades += len(engine.submit_order(sell))
        trades += len(engine.submit_order(buy))

    elapsed_ns = time.perf_counter_ns() - start

    orders = iterations * 2

    return orders, trades, elapsed_ns


def percentile(values, percentile):
    """
    Calculate a percentile using sorted benchmark samples.
    """
    values = sorted(values)

    if not values:
        return 0

    index = (len(values) - 1) * percentile / 100
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)

    fraction = index - lower

    return (
        values[lower]
        + (values[upper] - values[lower]) * fraction
    )


def test_matching_engine_benchmark():
    # --------------------------------------------------------------
    # Warm-up
    # --------------------------------------------------------------

    run_benchmark(5_000)

    # --------------------------------------------------------------
    # Measured runs
    # --------------------------------------------------------------

    runs = 10

    throughputs = []
    latencies_ns = []

    orders = 0
    trades = 0

    for _ in range(runs):
        orders, trades, elapsed_ns = run_benchmark(50_000)

        throughput = orders / (elapsed_ns / 1_000_000_000)
        latency_ns = elapsed_ns / orders

        throughputs.append(throughput)
        latencies_ns.append(latency_ns)

    # --------------------------------------------------------------
    # Statistics
    # --------------------------------------------------------------

    mean_throughput = mean(throughputs)
    min_throughput = min(throughputs)
    max_throughput = max(throughputs)

    median_latency = median(latencies_ns)
    p95_latency = percentile(latencies_ns, 95)
    p99_latency = percentile(latencies_ns, 99)
    p999_latency = percentile(latencies_ns, 99.9)

    min_latency = min(latencies_ns)
    max_latency = max(latencies_ns)

    # --------------------------------------------------------------
    # Output
    # --------------------------------------------------------------

    print()
    print("========== MATCHING ENGINE BENCHMARK ==========")

    print()
    print("Workload")
    print(f"  Orders processed : {orders:,}")
    print(f"  Trades generated : {trades:,}")
    print(f"  Measured runs    : {runs}")
    print("  Warm-up          : 5,000 iterations")

    print()
    print("Throughput")
    print(f"  Mean : {mean_throughput:,.0f} orders/sec")
    print(f"  Min  : {min_throughput:,.0f} orders/sec")
    print(f"  Max  : {max_throughput:,.0f} orders/sec")

    print()
    print("Latency")
    print(f"  Min   : {min_latency:,.0f} ns/order")
    print(f"  Median: {median_latency:,.0f} ns/order")
    print(f"  p95   : {p95_latency:,.0f} ns/order")
    print(f"  p99   : {p99_latency:,.0f} ns/order")
    print(f"  p99.9 : {p999_latency:,.0f} ns/order")
    print(f"  Max   : {max_latency:,.0f} ns/order")

    print()
    print("================================================")

    # --------------------------------------------------------------
    # Correctness check
    # --------------------------------------------------------------

    assert trades == 50_000