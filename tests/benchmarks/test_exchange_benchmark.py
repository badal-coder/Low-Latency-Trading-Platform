import time
from statistics import median

from engine.exchange import Exchange
from engine.gateway import OrderRequest
from engine.order import OrderType, Side


ACCOUNT_ID = 1
SYMBOL = "AAPL"
PRICE = 100
QUANTITY = 1


def make_request(
    order_id: int,
    side: Side,
    timestamp_ns: int,
) -> OrderRequest:
    return OrderRequest(
        order_id=order_id,
        account_id=ACCOUNT_ID,
        symbol=SYMBOL,
        side=side,
        order_type=OrderType.LIMIT,
        price=PRICE,
        quantity=QUANTITY,
        timestamp_ns=timestamp_ns,
    )


def run_benchmark(iterations: int = 50_000):
    """
    Benchmark the complete Exchange submission path:

        Exchange
          -> account lookup
          -> reservations
          -> gateway
          -> risk validation
          -> matching engine
          -> event bus
          -> settlement
          -> reservation updates

    Each iteration submits:

        1 SELL order
        1 BUY order

    The BUY matches the SELL, generating one trade.
    """

    exchange = Exchange()

    # ---------------------------------------------------------
    # Account setup
    # ---------------------------------------------------------

    account = exchange.create_account(
        account_id=ACCOUNT_ID,
        initial_cash=iterations * PRICE,
    )

    # Account uses update_position(), not deposit_position().
    account.update_position(
        SYMBOL,
        iterations,
    )

    # ---------------------------------------------------------
    # Benchmark
    # ---------------------------------------------------------

    start = time.perf_counter_ns()

    trades = 0

    for i in range(iterations):

        sell_order_id = (i * 2) + 1
        buy_order_id = (i * 2) + 2

        sell = make_request(
            order_id=sell_order_id,
            side=Side.SELL,
            timestamp_ns=sell_order_id,
        )

        buy = make_request(
            order_id=buy_order_id,
            side=Side.BUY,
            timestamp_ns=buy_order_id,
        )

        trades += len(
            exchange.submit_order(sell)
        )

        trades += len(
            exchange.submit_order(buy)
        )

    elapsed_ns = time.perf_counter_ns() - start

    orders = iterations * 2

    return orders, trades, elapsed_ns


def test_exchange_end_to_end_benchmark():

    # ---------------------------------------------------------
    # Warm-up
    # ---------------------------------------------------------

    run_benchmark(5_000)

    # ---------------------------------------------------------
    # Measured runs
    # ---------------------------------------------------------

    results = []

    measured_iterations = 50_000

    for _ in range(10):

        orders, trades, elapsed_ns = run_benchmark(
            measured_iterations
        )

        throughput = (
            orders
            / (elapsed_ns / 1_000_000_000)
        )

        latency_ns = elapsed_ns / orders

        results.append(
            (
                throughput,
                latency_ns,
            )
        )

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    throughputs = [
        throughput
        for throughput, _ in results
    ]

    latencies = [
        latency
        for _, latency in results
    ]

    avg_throughput = (
        sum(throughputs)
        / len(throughputs)
    )

    min_throughput = min(throughputs)
    max_throughput = max(throughputs)

    min_latency = min(latencies)
    median_latency = median(latencies)
    max_latency = max(latencies)

    # Percentiles
    sorted_latencies = sorted(latencies)

    def percentile(values, percentile):
        index = int(
            (len(values) - 1)
            * percentile
        )
        return values[index]

    p95_latency = percentile(
        sorted_latencies,
        0.95,
    )

    p99_latency = percentile(
        sorted_latencies,
        0.99,
    )

    p999_latency = percentile(
        sorted_latencies,
        0.999,
    )

    # ---------------------------------------------------------
    # Results
    # ---------------------------------------------------------

    print()
    print("========== EXCHANGE END-TO-END BENCHMARK ==========")
    print()
    print("Workload")
    print(f"  Orders processed : {orders:,}")
    print(f"  Trades generated : {trades:,}")
    print("  Measured runs    : 10")
    print("  Warm-up          : 5,000 iterations")
    print()
    print("Throughput")
    print(
        f"  Mean : {avg_throughput:,.0f} orders/sec"
    )
    print(
        f"  Min  : {min_throughput:,.0f} orders/sec"
    )
    print(
        f"  Max  : {max_throughput:,.0f} orders/sec"
    )
    print()
    print("Latency")
    print(
        f"  Min    : {min_latency:,.0f} ns/order"
    )
    print(
        f"  Median : {median_latency:,.0f} ns/order"
    )
    print(
        f"  p95    : {p95_latency:,.0f} ns/order"
    )
    print(
        f"  p99    : {p99_latency:,.0f} ns/order"
    )
    print(
        f"  p99.9  : {p999_latency:,.0f} ns/order"
    )
    print(
        f"  Max    : {max_latency:,.0f} ns/order"
    )
    print()
    print("=====================================================")
    print()

    # ---------------------------------------------------------
    # Correctness assertion
    # ---------------------------------------------------------

    # Every BUY matches exactly one SELL.
    assert trades == measured_iterations