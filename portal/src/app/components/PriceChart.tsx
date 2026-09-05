"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const API = "http://127.0.0.1:8001";
const SYMBOL = "BTC/USD";

type Trade = {
  price?: number;
  quantity?: number;
  qty?: number;
  timestamp?: string;
  time?: string;
};

type ChartPoint = {
  time: string;
  price: number;
};

export default function PriceChart() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);

  async function loadTrades() {
    try {
      const token = localStorage.getItem("exchange_token");

      const response = await fetch(
        `${API}/trades/${encodeURIComponent(SYMBOL)}`,
        {
          headers: token
            ? {
                Authorization: `Bearer ${token}`,
              }
            : {},
          cache: "no-store",
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      const list = Array.isArray(data)
        ? data
        : Array.isArray(data.trades)
        ? data.trades
        : [];

      setTrades(list);
    } catch (error) {
      console.error("Price chart error:", error);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTrades();

    const interval = setInterval(loadTrades, 1500);

    return () => clearInterval(interval);
  }, []);

  const chartData = useMemo<ChartPoint[]>(() => {
    return trades
      .map((trade, index) => {
        const price = Number(trade.price);

        if (!Number.isFinite(price)) {
          return null;
        }

        const rawTime =
          trade.timestamp ||
          trade.time ||
          new Date(Date.now() - (trades.length - index) * 1000).toISOString();

        const date = new Date(rawTime);

        return {
          time: Number.isNaN(date.getTime())
            ? `${index + 1}`
            : date.toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              }),
          price,
        };
      })
      .filter((item): item is ChartPoint => item !== null);
  }, [trades]);

  const latestPrice =
    chartData.length > 0
      ? chartData[chartData.length - 1].price
      : null;

  return (
    <div className="rounded-2xl border border-white/10 bg-[#111318] p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">
            BTC/USD Price
          </h2>
          <p className="text-xs text-gray-500">
            Live exchange trade price
          </p>
        </div>

        <div className="text-right">
          <div className="text-xl font-bold text-white">
            {latestPrice !== null
              ? `$${latestPrice.toLocaleString()}`
              : "--"}
          </div>

          <div className="text-xs text-green-400">
            ● LIVE
          </div>
        </div>
      </div>

      <div className="h-[320px] w-full">
        {loading ? (
          <div className="flex h-full items-center justify-center text-gray-500">
            Loading chart...
          </div>
        ) : chartData.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-gray-500">
            <div className="mb-2 text-3xl">📈</div>
            <div>No trades yet</div>
            <div className="mt-1 text-xs">
              Execute trades to populate the price chart
            </div>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={chartData}
              margin={{
                top: 10,
                right: 10,
                left: 0,
                bottom: 5,
              }}
            >
              <defs>
                <linearGradient
                  id="priceGradient"
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >
                  <stop
                    offset="0%"
                    stopColor="#22c55e"
                    stopOpacity={0.35}
                  />
                  <stop
                    offset="100%"
                    stopColor="#22c55e"
                    stopOpacity={0}
                  />
                </linearGradient>
              </defs>

              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#27272a"
              />

              <XAxis
                dataKey="time"
                stroke="#71717a"
                tick={{ fill: "#71717a", fontSize: 11 }}
                minTickGap={30}
              />

              <YAxis
                stroke="#71717a"
                tick={{ fill: "#71717a", fontSize: 11 }}
                domain={["auto", "auto"]}
                tickFormatter={(value) =>
                  `$${Number(value).toLocaleString()}`
                }
                width={85}
              />

              <Tooltip
                contentStyle={{
                  background: "#18181b",
                  border: "1px solid #3f3f46",
                  borderRadius: "10px",
                  color: "#fff",
                }}
                formatter={(value: number | undefined) => [
                  value !== undefined
                    ? `$${Number(value).toLocaleString()}`
                    : "--",
                  "Price",
                ]}
              />

              <Area
                type="monotone"
                dataKey="price"
                stroke="#22c55e"
                strokeWidth={2}
                fill="url(#priceGradient)"
                dot={false}
                activeDot={{
                  r: 5,
                }}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="mt-3 flex justify-between border-t border-white/5 pt-3 text-xs text-gray-500">
        <span>{chartData.length} trades</span>
        <span>Updates every 1.5s</span>
      </div>
    </div>
  );
}