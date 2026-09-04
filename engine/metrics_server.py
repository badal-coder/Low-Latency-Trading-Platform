from __future__ import annotations

import argparse
import threading
import time

from prometheus_client import start_http_server

from .exchange import Exchange
from .gateway import OrderRequest
from .order import OrderType, Side


DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000

DEFAULT_RATE = 200
DEFAULT_SYMBOL = "AAPL"
DEFAULT_PRICE = 100
DEFAULT_QUANTITY = 1

SELLER_ID = 1
BUYER_ID = 2


def generate_demo_traffic(
    exchange: Exchange,
    rate: int,
    symbol: str,
    price: int,
    quantity: int,
) -> None:
    """
    Generate continuous exchange traffic for local observability.

    Each iteration submits:
        1 SELL order
        1 BUY order

    The BUY crosses the SELL, generating a trade.

    rate = total orders/sec.
    """

    if rate <= 0:
        raise ValueError("rate must be greater than zero")

    # ---------------------------------------------------------
    # Accounts
    # ---------------------------------------------------------

    exchange.create_account(
        account_id=SELLER_ID,
        initial_cash=0,
    )

    seller = exchange.accounts.get_account(SELLER_ID)

    seller.update_position(
        symbol,
        1_000_000,
    )

    exchange.create_account(
        account_id=BUYER_ID,
        initial_cash=100_000_000,
    )

    # ---------------------------------------------------------
    # Rate control
    # ---------------------------------------------------------

    # One iteration creates two orders.
    orders_per_pair = 2

    pair_rate = max(rate / orders_per_pair, 1)

    interval = 1.0 / pair_rate

    order_id = 1

    next_run = time.perf_counter()

    print()
    print("----------------------------------------------")
    print("DEMO TRAFFIC STARTED")
    print(f"Target orders/sec : {rate}")
    print(f"Target trades/sec : {rate / 2:.1f}")
    print(f"Symbol            : {symbol}")
    print("----------------------------------------------")
    print()

    # ---------------------------------------------------------
    # Continuous workload
    # ---------------------------------------------------------

    while True:
        next_run += interval

        sell_timestamp = time.perf_counter_ns()

        sell = OrderRequest(
            order_id=order_id,
            account_id=SELLER_ID,
            symbol=symbol,
            side=Side.SELL,
            order_type=OrderType.LIMIT,
            price=price,
            quantity=quantity,
            timestamp_ns=sell_timestamp,
        )

        buy_timestamp = time.perf_counter_ns()

        buy = OrderRequest(
            order_id=order_id + 1,
            account_id=BUYER_ID,
            symbol=symbol,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            price=price,
            quantity=quantity,
            timestamp_ns=buy_timestamp,
        )

        try:
            exchange.submit_order(sell)
            exchange.submit_order(buy)

        except Exception as exc:
            print(f"Demo order error: {exc}")

        order_id += orders_per_pair

        # -----------------------------------------------------
        # Precise rate limiting
        # -----------------------------------------------------

        sleep_time = next_run - time.perf_counter()

        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            # Workload took longer than the target interval.
            # Reset the schedule instead of accumulating lag.
            next_run = time.perf_counter()


def start_metrics_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    rate: int = DEFAULT_RATE,
    symbol: str = DEFAULT_SYMBOL,
    price: int = DEFAULT_PRICE,
    quantity: int = DEFAULT_QUANTITY,
) -> None:
    """
    Start Prometheus metrics and the exchange demo workload.
    """

    exchange = Exchange()

    # ---------------------------------------------------------
    # Prometheus
    # ---------------------------------------------------------

    start_http_server(
        port=port,
        addr=host,
    )

    print()
    print("==============================================")
    print(" LOW-LATENCY EXCHANGE OBSERVABILITY SERVICE")
    print("==============================================")
    print(f"Metrics : http://127.0.0.1:{port}/metrics")
    print(f"Symbol  : {symbol}")
    print(f"Rate    : {rate} orders/sec")
    print("Demo traffic: ENABLED")
    print("==============================================")
    print()

    # ---------------------------------------------------------
    # Background workload
    # ---------------------------------------------------------

    worker = threading.Thread(
        target=generate_demo_traffic,
        kwargs={
            "exchange": exchange,
            "rate": rate,
            "symbol": symbol,
            "price": price,
            "quantity": quantity,
        },
        daemon=True,
        name="exchange-demo-traffic",
    )

    worker.start()

    # ---------------------------------------------------------
    # Keep service alive
    # ---------------------------------------------------------

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping exchange...")

    finally:
        exchange.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the exchange observability service."
    )

    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help="Metrics HTTP bind address.",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Metrics HTTP port.",
    )

    parser.add_argument(
        "--rate",
        type=int,
        default=DEFAULT_RATE,
        help="Target total orders per second.",
    )

    parser.add_argument(
        "--symbol",
        default=DEFAULT_SYMBOL,
        help="Trading symbol.",
    )

    parser.add_argument(
        "--price",
        type=int,
        default=DEFAULT_PRICE,
        help="Limit order price.",
    )

    parser.add_argument(
        "--quantity",
        type=int,
        default=DEFAULT_QUANTITY,
        help="Order quantity.",
    )

    args = parser.parse_args()

    start_metrics_server(
        host=args.host,
        port=args.port,
        rate=args.rate,
        symbol=args.symbol,
        price=args.price,
        quantity=args.quantity,
    )


if __name__ == "__main__":
    main()