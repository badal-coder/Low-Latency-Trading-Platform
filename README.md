# Low-Latency Exchange Engine

A Python-based exchange simulation focused on **low-latency order processing, matching, persistence, recovery, and observability**.

The system implements an in-memory matching engine with price-time priority, order lifecycle management, risk controls, reservations, trade settlement, WAL persistence, crash recovery, and Prometheus/Grafana monitoring.

## Architecture

```text
                    +------------------+
                    |  Order Gateway   |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |     Exchange     |
                    |------------------|
                    | Validation/Risk  |
                    | Reservations     |
                    | Settlement       |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    | Matching Engine  |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |    Order Book    |
                    | Price-Time        |
                    | Priority          |
                    +--------+---------+
                             |
              +--------------+--------------+
              |                             |
              v                             v
       +-------------+              +--------------+
       |   Trades    |              | Event Bus/WAL|
       | Settlement  |              | Persistence  |
       +-------------+              +------+-------+
                                           |
                                           v
                                    +-------------+
                                    |  Recovery   |
                                    +-------------+

Observability:

Exchange → Prometheus → Grafana
```
