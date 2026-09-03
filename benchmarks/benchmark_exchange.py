import time
import statistics

from engine.exchange import Exchange
from engine.gateway import OrderRequest
from engine.order import Side, OrderType


def benchmark(num_orders: int = 10_000) -> None:
    exchange = Exchange()

    exchange.create_account(
        account_id=1,
        initial_cash=10_000_000,
    )

    exchange.create_account(
        account_id=2,
        initial_cash=0,
    )

    # Put liquidity on the book.
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

    latencies_ns = []

    for i in range(num_orders):
        order_id = i + 2

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
    print("===== Exchange Benchmark =====")
    print(f"Orders:       {num_orders:,}")
    print(f"Throughput:   {throughput:,.0f} orders/sec")
    print(f"p50 latency:  {p50:.2f} us")
    print(f"p95 latency:  {p95:.2f} us")
    print(f"p99 latency:  {p99:.2f} us")
    print(f"Max latency:  {maximum:.2f} us")
    print("==============================")
    print()


if __name__ == "__main__":
    benchmark()