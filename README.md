# Low-Latency Exchange

A low-latency financial exchange simulation implementing a deterministic
price-time-priority matching engine, order book management, risk validation,
event-driven architecture, order lifecycle management, persistence, recovery,
and performance benchmarking.

The project is designed to explore the core engineering problems behind
electronic trading systems: deterministic matching, FIFO execution,
low-latency order processing, risk controls, event sequencing, durability,
and crash recovery.

---

## 🚀 Current Performance

The matching engine was benchmarked with 20,000 orders generating 10,000 trades.

| Metric             |              Result |
| ------------------ | ------------------: |
| Orders processed   |              20,000 |
| Trades generated   |              10,000 |
| Average throughput | ~150,000 orders/sec |
| Average latency    |       ~6.7 µs/order |
| Test suite         |          158 passed |

Example benchmark:

```text
========== MATCHING ENGINE BENCHMARK ==========
Orders processed : 20,000
Trades generated : 10,000
Average throughput: 150,829 orders/sec
Average latency   : 6,733 ns/order
===============================================
```
