import statistics
import time

from engine.exchange import Exchange
from engine.gateway import OrderRequest
from engine.order import Side, OrderType


def run_benchmark(
    name: str,
    exchange: Exchange,
    num_orders: int,
) -> None:

    latencies_ns = []

    for i in range(num_orders):
        order_id = i + 10_000

        request = OrderRequest(
            order_id=order_id,
            account_id=1,
            symbol="AAPL",
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            quantity=1,
            price=100,
            timestamp_ns=time.time_ns(),
        )

        start = time.perf_counter_ns()

        exchange.submit_order(request)

        end = time.perf_counter_ns()

        latencies_ns.append(end - start)

    latencies_us = [
        latency / 1_000
        for latency in latencies_ns
    ]

    latencies_us.sort()

    p50 = statistics.median(latencies_us)
    p95 = latencies_us[int(len(latencies_us) * 0.95)]
    p99 = latencies_us[int(len(latencies_us) * 0.99)]
    maximum = max(latencies_us)

    total_seconds = sum(latencies_ns) / 1_000_000_000
    throughput = num_orders / total_seconds

    print()
    print(f"===== {name} =====")
    print(f"Orders:       {num_orders:,}")
    print(f"Throughput:   {throughput:,.0f} orders/sec")
    print(f"p50 latency:  {p50:.2f} us")
    print(f"p95 latency:  {p95:.2f} us")
    print(f"p99 latency:  {p99:.2f} us")
    print(f"Max latency:  {maximum:.2f} us")
    print("==============================")
    print()


def create_exchange() -> Exchange:
    exchange = Exchange()

    exchange.create_account(
        account_id=1,
        initial_cash=10_000_000,
    )

    exchange.create_account(
        account_id=2,
        initial_cash=0,
    )

    return exchange


def setup_single_level(
    exchange: Exchange,
    num_orders: int,
) -> None:

    exchange.submit_order(
        OrderRequest(
            order_id=1,
            account_id=2,
            symbol="AAPL",
            side=Side.SELL,
            order_type=OrderType.LIMIT,
            quantity=num_orders,
            price=100,
            timestamp_ns=time.time_ns(),
        )
    )


def setup_many_levels(
    exchange: Exchange,
) -> None:

    order_id = 1

    # Create many ask price levels.
    for price in range(100, 1_100):
        exchange.submit_order(
            OrderRequest(
                order_id=order_id,
                account_id=2,
                symbol="AAPL",
                side=Side.SELL,
                order_type=OrderType.LIMIT,
                quantity=1,
                price=price,
                timestamp_ns=time.time_ns(),
            )
        )

        order_id += 1


def main() -> None:

    num_orders = 10_000

    # --------------------------------------------------
    # Benchmark A: single price level
    # --------------------------------------------------

    exchange = create_exchange()

    setup_single_level(
        exchange,
        num_orders,
    )

    run_benchmark(
        "Single Price Level Benchmark",
        exchange,
        num_orders,
    )

    # --------------------------------------------------
    # Benchmark B: many price levels
    # --------------------------------------------------

    exchange = create_exchange()

    setup_many_levels(exchange)

    run_benchmark(
        "Many Price Levels Benchmark",
        exchange,
        num_orders,
    )


if __name__ == "__main__":
    main()