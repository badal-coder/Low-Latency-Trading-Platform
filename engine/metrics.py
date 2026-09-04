from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram


# =============================================================
# ORDER METRICS
# =============================================================

orders_total = Counter(
    "exchange_orders_total",
    "Total number of orders submitted to the exchange",
    ["side", "order_type"],
)

orders_rejected_total = Counter(
    "exchange_orders_rejected_total",
    "Total number of rejected orders",
)

orders_cancelled_total = Counter(
    "exchange_orders_cancelled_total",
    "Total number of cancelled orders",
)


# =============================================================
# TRADE METRICS
# =============================================================

trades_total = Counter(
    "exchange_trades_total",
    "Total number of trades executed",
)

trade_volume_total = Counter(
    "exchange_trade_volume_total",
    "Total quantity traded by the exchange",
)


# =============================================================
# LATENCY METRICS
# =============================================================

order_latency_seconds = Histogram(
    "exchange_order_latency_seconds",
    "End-to-end order processing latency",
    buckets=(
        0.000001,
        0.000002,
        0.000005,
        0.000010,
        0.000025,
        0.000050,
        0.000100,
        0.000250,
        0.001,
        0.005,
        0.010,
        0.025,
        0.100,
    ),
)


# =============================================================
# EXCHANGE STATE
# =============================================================

active_orders = Gauge(
    "exchange_active_orders",
    "Number of currently active orders",
)


# =============================================================
# WAL
# =============================================================

wal_events_total = Counter(
    "exchange_wal_events_total",
    "Total number of events written to the WAL",
)