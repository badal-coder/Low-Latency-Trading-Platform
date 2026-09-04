import cProfile
import pstats

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


def benchmark():
    engine = MatchingEngine()

    iterations = 10_000

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
        engine.submit_order(buy)


if __name__ == "__main__":
    profiler = cProfile.Profile()

    profiler.enable()
    benchmark()
    profiler.disable()

    stats = pstats.Stats(profiler)
    stats.sort_stats("cumulative")
    stats.print_stats(30)