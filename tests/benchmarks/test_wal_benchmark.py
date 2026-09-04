import statistics
import tempfile
import time
from pathlib import Path

from engine.exchange import Exchange
from engine.gateway import OrderRequest
from engine.order import OrderType, Side


SYMBOL = "AAPL"
ACCOUNT_ID = 1
PRICE = 100
QUANTITY = 1


def percentile(values, p):
    values = sorted(values)

    if not values:
        return 0

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


def run_benchmark(
    iterations: int = 2_000,
    *,
    wal_path=None,
    wal_fsync: bool = False,
):
    """
    Benchmark the complete Exchange path.

    Path:

        Exchange
          -> reservations
          -> gateway
          -> risk validation
          -> matching engine
          -> event bus
          -> settlement
          -> reservation updates
          -> optional WAL persistence
    """

    exchange = Exchange(
        wal_path=wal_path,
        wal_fsync=wal_fsync,
    )

    # Give the account enough cash for BUY orders.
    account = exchange.create_account(
        account_id=ACCOUNT_ID,
        initial_cash=iterations * PRICE,
    )

    # Give the account enough inventory for SELL orders.
    account.update_position(
        SYMBOL,
        iterations,
    )

    latencies = []
    trades = 0

    try:
        start = time.perf_counter_ns()

        for i in range(iterations):

            sell_id = (i * 2) + 1
            buy_id = (i * 2) + 2

            sell = make_request(
                sell_id,
                Side.SELL,
                sell_id,
            )

            buy = make_request(
                buy_id,
                Side.BUY,
                buy_id,
            )

            # Measure the complete exchange processing
            # for one SELL + one BUY pair.
            order_start = time.perf_counter_ns()

            trades += len(
                exchange.submit_order(sell)
            )

            trades += len(
                exchange.submit_order(buy)
            )

            order_end = time.perf_counter_ns()

            # Two orders were processed.
            latencies.append(
                (order_end - order_start) / 2
            )

        elapsed_ns = (
            time.perf_counter_ns() - start
        )

    finally:
        exchange.close()

    orders = iterations * 2

    throughput = (
        orders
        / (elapsed_ns / 1_000_000_000)
    )

    return {
        "orders": orders,
        "trades": trades,
        "throughput": throughput,
        "latencies": latencies,
    }


def print_result(
    name: str,
    result: dict,
) -> None:

    latencies = result["latencies"]

    print()
    print(f"--- {name} ---")

    print("Throughput")
    print(
        f"  Mean : "
        f"{result['throughput']:,.0f} orders/sec"
    )

    print("Latency")
    print(
        f"  Min    : "
        f"{min(latencies):,.0f} ns/order"
    )

    print(
        f"  Median : "
        f"{statistics.median(latencies):,.0f} ns/order"
    )

    print(
        f"  p95    : "
        f"{percentile(latencies, 0.95):,.0f} ns/order"
    )

    print(
        f"  p99    : "
        f"{percentile(latencies, 0.99):,.0f} ns/order"
    )

    print(
        f"  Max    : "
        f"{max(latencies):,.0f} ns/order"
    )


def test_wal_persistence_benchmark():

    # ---------------------------------------------------------
    # Normal benchmark workload
    # ---------------------------------------------------------

    iterations = 2_000

    # ---------------------------------------------------------
    # Warm-up
    # ---------------------------------------------------------

    run_benchmark(500)

    # ---------------------------------------------------------
    # NO WAL
    # ---------------------------------------------------------

    no_wal = run_benchmark(
        iterations,
        wal_path=None,
        wal_fsync=False,
    )

    # ---------------------------------------------------------
    # WAL WITHOUT FSYNC
    # ---------------------------------------------------------

    with tempfile.TemporaryDirectory() as tmp:

        wal_path = Path(tmp) / "exchange.wal"

        wal_no_fsync = run_benchmark(
            iterations,
            wal_path=wal_path,
            wal_fsync=False,
        )

    # ---------------------------------------------------------
    # WAL WITH FSYNC
    #
    # fsync is intentionally expensive.
    # Use a smaller workload so the benchmark remains practical.
    # ---------------------------------------------------------

    fsync_iterations = 250

    with tempfile.TemporaryDirectory() as tmp:

        wal_path = Path(tmp) / "exchange.wal"

        wal_fsync = run_benchmark(
            fsync_iterations,
            wal_path=wal_path,
            wal_fsync=True,
        )

    # ---------------------------------------------------------
    # REPORT
    # ---------------------------------------------------------

    print()
    print("========== WAL PERSISTENCE BENCHMARK ==========")

    print()
    print("Workload")
    print(
        f"  Normal orders/run : "
        f"{no_wal['orders']:,}"
    )

    print(
        f"  Normal trades/run : "
        f"{no_wal['trades']:,}"
    )

    print(
        f"  fsync orders/run  : "
        f"{wal_fsync['orders']:,}"
    )

    # ---------------------------------------------------------
    # NO WAL
    # ---------------------------------------------------------

    print_result(
        "NO WAL",
        no_wal,
    )

    # ---------------------------------------------------------
    # WAL NO FSYNC
    # ---------------------------------------------------------

    print_result(
        "WAL (fsync=False)",
        wal_no_fsync,
    )

    # ---------------------------------------------------------
    # WAL FSYNC
    # ---------------------------------------------------------

    print_result(
        "WAL (fsync=True)",
        wal_fsync,
    )

    # ---------------------------------------------------------
    # Persistence overhead
    # ---------------------------------------------------------

    no_wal_throughput = (
        no_wal["throughput"]
    )

    no_fsync_throughput = (
        wal_no_fsync["throughput"]
    )

    fsync_throughput = (
        wal_fsync["throughput"]
    )

    no_fsync_overhead = (
        1
        - (
            no_fsync_throughput
            / no_wal_throughput
        )
    ) * 100

    fsync_overhead = (
        1
        - (
            fsync_throughput
            / no_wal_throughput
        )
    ) * 100

    print()
    print("Persistence overhead")

    print(
        f"  WAL fsync=False : "
        f"{no_fsync_overhead:.2f}%"
    )

    print(
        f"  WAL fsync=True  : "
        f"{fsync_overhead:.2f}%"
    )

    print()
    print("===============================================")

    # ---------------------------------------------------------
    # Correctness checks
    # ---------------------------------------------------------

    assert no_wal["trades"] == iterations

    assert (
        wal_no_fsync["trades"]
        == iterations
    )

    assert (
        wal_fsync["trades"]
        == fsync_iterations
    )