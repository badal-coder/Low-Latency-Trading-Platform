import time

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


def test_matching_engine_throughput():
    engine = MatchingEngine()

    iterations = 10_000

    start = time.perf_counter_ns()

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

        engine.submit_order(sell)
        trades = engine.submit_order(buy)

        assert len(trades) == 1

    elapsed_ns = time.perf_counter_ns() - start

    orders = iterations * 2

    print()
    print("========== MATCHING ENGINE BENCHMARK ==========")
    print(f"Orders processed : {orders:,}")
    print(f"Trades generated : {iterations:,}")
    print(f"Total time       : {elapsed_ns / 1_000_000:.3f} ms")
    print(
        f"Throughput       : "
        f"{orders / (elapsed_ns / 1_000_000_000):,.0f} orders/sec"
    )
    print(f"Avg latency      : {elapsed_ns / orders:,.0f} ns/order")
    print("===============================================")