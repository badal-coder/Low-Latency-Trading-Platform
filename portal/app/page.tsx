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
const WS_URL = "ws://127.0.0.1:8001/ws";
const SYMBOL = "BTC/USD";
const TOKEN_KEY = "exchange_token";

type User = {
  id: number;
  username: string;
};

type Account = {
  account_id: number;
  cash: number;
  available_cash: number;
  reserved_cash: number;
  positions: Record<string, number>;
  reserved_positions: Record<string, number>;
};

type PortfolioPosition = {
  symbol: string;
  quantity: number;
  market_price: number;
  market_value: number;
};

type Portfolio = {
  account_id: number;
  cash: number;
  available_cash: number;
  reserved_cash: number;
  market_value: number;
  portfolio_value: number;
  equity: number;
  total_value: number;
  total_pnl: number;
  positions: PortfolioPosition[];
};

type Order = {
  order_id: number;
  account_id: number;
  symbol: string;
  side: string;
  order_type: string;
  price: number;
  quantity: number;
  filled_quantity: number;
  remaining_quantity: number;
  status: string;
  timestamp_ns: number;
};

type BookLevel = {
  price: number;
  quantity: number;
};

type Trade = {
  trade_id: number;
  symbol: string;
  buy_order_id: number;
  sell_order_id: number;
  price: number;
  quantity: number;
  timestamp_ns: number;
};

type Execution = {
  trade_id: number;
  symbol: string;
  side: string;
  order_id: number;
  price: number;
  quantity: number;
  timestamp_ns: number;
};

type ChartPoint = {
  time: string;
  price: number;
};

function token() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

async function apiFetch(path: string, options: RequestInit = {}, auth = true) {
  const headers = new Headers(options.headers || {});

  headers.set("Content-Type", "application/json");

  if (auth) {
    const currentToken = token();

    if (currentToken) {
      headers.set("Authorization", `Bearer ${currentToken}`);
    }
  }

  let response: Response;

  try {
    response = await fetch(`${API}${path}`, {
      ...options,
      headers,
    });
  } catch {
    throw new Error(`Cannot connect to Exchange API at ${API}`);
  }

  const text = await response.text();

  let data: any = null;

  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }

  if (!response.ok) {
    if (response.status === 401 && auth) {
      localStorage.removeItem(TOKEN_KEY);
    }

    throw new Error(
      data?.detail || data?.message || `API error ${response.status}`,
    );
  }

  return data;
}

function money(value: number | undefined | null) {
  return Number(value || 0).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function quantity(value: number | undefined | null) {
  return Number(value || 0).toLocaleString("en-US", {
    maximumFractionDigits: 8,
  });
}

function timeFromNs(ns: number) {
  if (!ns) return "--";

  return new Date(Number(ns) / 1_000_000).toLocaleTimeString();
}

/* ============================================================
   AUTH SCREEN
============================================================ */

function AuthScreen({
  onAuthenticated,
}: {
  onAuthenticated: (user: User) => void;
}) {
  const [mode, setMode] = useState<"login" | "signup">("login");

  const [username, setUsername] = useState("");

  const [password, setPassword] = useState("");

  const [initialCash, setInitialCash] = useState("1000000");

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();

    setError("");

    if (!username.trim()) {
      setError("Username is required.");
      return;
    }

    if (password.length < 6) {
      setError("Password must contain at least 6 characters.");
      return;
    }

    setLoading(true);

    try {
      const endpoint = mode === "login" ? "/auth/login" : "/auth/signup";

      const body =
        mode === "login"
          ? {
              username: username.trim(),
              password,
            }
          : {
              username: username.trim(),
              password,
              initial_cash: Number(initialCash) || 0,
            };

      const data = await apiFetch(
        endpoint,
        {
          method: "POST",
          body: JSON.stringify(body),
        },
        false,
      );

      localStorage.setItem(TOKEN_KEY, data.access_token);

      onAuthenticated(data.user);
    } catch (error: any) {
      setError(error?.message || "Authentication failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#070b12] text-white flex items-center justify-center px-6">
      <div className="w-full max-w-[560px]">
        <div className="flex justify-center items-center gap-3 mb-7">
          <div className="h-12 w-12 rounded-2xl bg-blue-600 flex items-center justify-center text-xl font-bold">
            LX
          </div>

          <div className="text-2xl font-bold">Low Latency Exchange</div>
        </div>

        <h1 className="text-center text-4xl font-bold">
          {mode === "login" ? "Welcome back" : "Create account"}
        </h1>

        <p className="text-center text-gray-500 text-lg mt-2 mb-10">
          Professional trading portal
        </p>

        <form
          onSubmit={submit}
          className="rounded-2xl border border-[#253044] bg-[#0d131d] p-8"
        >
          {error && (
            <div className="rounded-xl border border-red-800 bg-red-950/40 text-red-300 px-5 py-4 mb-6">
              {error}
            </div>
          )}

          <label className="block text-gray-400 mb-2">Username</label>

          <input
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            className="w-full rounded-xl border border-[#29364a] bg-[#080d15] px-5 py-4 text-lg outline-none focus:border-blue-500 mb-7"
            placeholder="Username"
            autoComplete="username"
          />

          <label className="block text-gray-400 mb-2">Password</label>

          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="w-full rounded-xl border border-[#29364a] bg-[#080d15] px-5 py-4 text-lg outline-none focus:border-blue-500 mb-7"
            placeholder="Password"
            autoComplete={
              mode === "login" ? "current-password" : "new-password"
            }
          />

          {mode === "signup" && (
            <>
              <label className="block text-gray-400 mb-2">Initial Cash</label>

              <input
                type="number"
                value={initialCash}
                onChange={(event) => setInitialCash(event.target.value)}
                className="w-full rounded-xl border border-[#29364a] bg-[#080d15] px-5 py-4 text-lg outline-none focus:border-blue-500 mb-7"
              />
            </>
          )}

          <button
            disabled={loading}
            className="w-full rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 py-4 text-xl font-bold"
          >
            {loading
              ? "Please wait..."
              : mode === "login"
                ? "Sign in"
                : "Create account"}
          </button>

          <div className="text-center mt-8 text-gray-500">
            {mode === "login" ? (
              <>
                Don't have an account?{" "}
                <button
                  type="button"
                  onClick={() => {
                    setMode("signup");
                    setError("");
                  }}
                  className="text-blue-400"
                >
                  Create one
                </button>
              </>
            ) : (
              <>
                Already have an account?{" "}
                <button
                  type="button"
                  onClick={() => {
                    setMode("login");
                    setError("");
                  }}
                  className="text-blue-400"
                >
                  Sign in
                </button>
              </>
            )}
          </div>
        </form>

        <div className="text-center text-gray-600 mt-7">
          Exchange API: {API}
        </div>
      </div>
    </main>
  );
}

/* ============================================================
   SECTION
============================================================ */

function Section({
  title,
  children,
  right,
}: {
  title: string;
  children: React.ReactNode;
  right?: React.ReactNode;
}) {
  return (
    <section className="rounded-xl border border-[#222d3d] bg-[#0d131d] overflow-hidden">
      <div className="px-5 py-4 border-b border-[#222d3d] flex items-center justify-between">
        <h2 className="font-semibold">{title}</h2>

        {right}
      </div>

      <div className="p-5">{children}</div>
    </section>
  );
}

/* ============================================================
   STAT
============================================================ */

function Stat({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-xl border border-[#222d3d] bg-[#0d131d] p-5">
      <div className="text-xs text-gray-500">{title}</div>

      <div className="text-2xl font-bold mt-2">{value}</div>
    </div>
  );
}

/* ============================================================
   MAIN
============================================================ */

export default function Home() {
  const [user, setUser] = useState<User | null>(null);

  const [booting, setBooting] = useState(true);

  const [accounts, setAccounts] = useState<Account[]>([]);

  const [accountId, setAccountId] = useState<number | null>(null);

  const [account, setAccount] = useState<Account | null>(null);

  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);

  const [bids, setBids] = useState<BookLevel[]>([]);

  const [asks, setAsks] = useState<BookLevel[]>([]);

  const [trades, setTrades] = useState<Trade[]>([]);

  const [orders, setOrders] = useState<Order[]>([]);

  const [executions, setExecutions] = useState<Execution[]>([]);

  const [side, setSide] = useState<"BUY" | "SELL">("BUY");

  const [orderType, setOrderType] = useState<"LIMIT" | "MARKET">("LIMIT");

  const [orderPrice, setOrderPrice] = useState("");

  const [orderQuantity, setOrderQuantity] = useState("");

  const [cashAction, setCashAction] = useState<"deposit" | "withdraw">(
    "deposit",
  );

  const [cashAmount, setCashAmount] = useState("");

  const [initialCash, setInitialCash] = useState("1000000");

  const [loading, setLoading] = useState(false);

  const [cashLoading, setCashLoading] = useState(false);

  const [accountLoading, setAccountLoading] = useState(false);

  const [error, setError] = useState("");

  const [message, setMessage] = useState("");

  const [connected, setConnected] = useState(false);

  const [wsConnected, setWsConnected] = useState(false);

  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  /* ==========================================================
     RESTORE SESSION
  ========================================================== */

  useEffect(() => {
    let alive = true;

    async function restore() {
      const savedToken = token();

      if (!savedToken) {
        if (alive) {
          setBooting(false);
        }

        return;
      }

      try {
        const data = await apiFetch("/auth/me");

        if (!alive) return;

        setUser(data.user);
      } catch {
        if (alive) {
          localStorage.removeItem(TOKEN_KEY);

          setUser(null);
        }
      } finally {
        if (alive) {
          setBooting(false);
        }
      }
    }

    restore();

    return () => {
      alive = false;
    };
  }, []);

  /* ==========================================================
     HEALTH
  ========================================================== */

  async function checkHealth() {
    try {
      await apiFetch("/health", {}, false);

      setConnected(true);
    } catch {
      setConnected(false);
    }
  }

  /* ==========================================================
     ACCOUNTS
  ========================================================== */

  async function fetchAccounts() {
    const data = await apiFetch("/accounts");

    const list: Account[] = data.accounts || [];

    setAccounts(list);

    if (list.length > 0 && accountId === null) {
      setAccountId(list[0].account_id);
    }
  }

  /* ==========================================================
     ACCOUNT
  ========================================================== */

  async function fetchAccount(id: number) {
    const data = await apiFetch(`/account/${id}`);

    setAccount(data);
  }

  /* ==========================================================
     PORTFOLIO
  ========================================================== */

  async function fetchPortfolio(id: number) {
    const data = await apiFetch(`/portfolio/${id}`);

    setPortfolio(data);
  }

  /* ==========================================================
     ORDER BOOK
  ========================================================== */

  async function fetchOrderBook() {
    const data = await apiFetch(`/orderbook/${encodeURIComponent(SYMBOL)}`);

    setBids(data.bids || []);

    setAsks(data.asks || []);
  }

  /* ==========================================================
     TRADES
  ========================================================== */

  async function fetchTrades() {
    const data = await apiFetch(`/trades/${encodeURIComponent(SYMBOL)}`);

    setTrades(data.trades || []);
  }

  /* ==========================================================
     ORDERS
  ========================================================== */

  async function fetchOrders() {
    const data = await apiFetch("/orders");

    setOrders(data.orders || []);
  }

  /* ==========================================================
     EXECUTIONS
  ========================================================== */

  async function fetchExecutions(id: number) {
    const data = await apiFetch(`/executions/${id}`);

    setExecutions(data.executions || []);
  }

  /* ==========================================================
     REFRESH
  ========================================================== */

  async function refresh() {
    try {
      await checkHealth();

      await fetchAccounts();

      await fetchOrderBook();

      await fetchTrades();

      if (accountId !== null) {
        await Promise.all([
          fetchAccount(accountId),
          fetchPortfolio(accountId),
          fetchOrders(),
          fetchExecutions(accountId),
        ]);
      }

      setLastUpdate(new Date());
    } catch (error: any) {
      console.error("Refresh failed:", error);
    }
  }

  /* ==========================================================
     POLLING
  ========================================================== */

  useEffect(() => {
    if (!user) return;

    refresh();

    const timer = window.setInterval(refresh, 1500);

    return () => window.clearInterval(timer);
  }, [user, accountId]);

  /* ==========================================================
     WEBSOCKET
  ========================================================== */

  useEffect(() => {
    if (!user) return;

    let ws: WebSocket | null = null;

    let reconnect: number | null = null;

    let stopped = false;

    function connect() {
      if (stopped) return;

      try {
        ws = new WebSocket(WS_URL);

        ws.onopen = () => {
          setWsConnected(true);
        };

        ws.onclose = () => {
          setWsConnected(false);

          if (!stopped) {
            reconnect = window.setTimeout(connect, 2000);
          }
        };

        ws.onerror = () => {
          setWsConnected(false);
        };

        ws.onmessage = () => {
          fetchOrderBook();
          fetchTrades();

          if (accountId !== null) {
            fetchAccount(accountId);

            fetchPortfolio(accountId);

            fetchOrders();

            fetchExecutions(accountId);
          }
        };
      } catch {
        setWsConnected(false);
      }
    }

    connect();

    return () => {
      stopped = true;

      if (reconnect !== null) {
        window.clearTimeout(reconnect);
      }

      ws?.close();
    };
  }, [user, accountId]);

  /* ==========================================================
     MARKET DATA
  ========================================================== */

  const bestBid = bids.length > 0 ? Number(bids[0].price) : 0;

  const bestAsk = asks.length > 0 ? Number(asks[0].price) : 0;

  const lastTrade = trades.length > 0 ? trades[trades.length - 1] : null;

  const marketPrice =
    lastTrade?.price ||
    (bestBid && bestAsk ? (bestBid + bestAsk) / 2 : bestBid || bestAsk);

  const chartData: ChartPoint[] = useMemo(
    () =>
      trades.slice(-100).map((trade, index) => ({
        time: trade.timestamp_ns
          ? new Date(trade.timestamp_ns / 1_000_000).toLocaleTimeString()
          : String(index),
        price: Number(trade.price),
      })),
    [trades],
  );

  const bidVolume = bids.reduce(
    (sum, level) => sum + Number(level.quantity),
    0,
  );

  const askVolume = asks.reduce(
    (sum, level) => sum + Number(level.quantity),
    0,
  );

  /* ==========================================================
     ORDER
  ========================================================== */

  async function submitOrder(event: React.FormEvent) {
    event.preventDefault();

    setError("");
    setMessage("");

    if (accountId === null) {
      setError("Select an account first.");
      return;
    }

    const qty = Number(orderQuantity);

    const price = Number(orderPrice);

    if (!qty || qty <= 0) {
      setError("Enter a valid quantity.");
      return;
    }

    if (orderType === "LIMIT" && (!price || price <= 0)) {
      setError("Enter a valid limit price.");
      return;
    }

    setLoading(true);

    try {
      const data = await apiFetch("/orders", {
        method: "POST",
        body: JSON.stringify({
          account_id: accountId,
          symbol: SYMBOL,
          side,
          order_type: orderType,
          quantity: qty,
          price: orderType === "LIMIT" ? price : 0,
        }),
      });

      setMessage(`Order #${data.order_id} accepted • ${data.trades} trade(s)`);

      setOrderQuantity("");

      await refresh();
    } catch (error: any) {
      setError(error?.message || "Order failed.");
    } finally {
      setLoading(false);
    }
  }

  /* ==========================================================
     CANCEL
  ========================================================== */

  async function cancelOrder(order: Order) {
    setError("");
    setMessage("");

    try {
      await apiFetch(
        `/orders/${encodeURIComponent(order.symbol)}/${order.order_id}`,
        {
          method: "DELETE",
        },
      );

      setMessage(`Order #${order.order_id} cancelled.`);

      await refresh();
    } catch (error: any) {
      setError(error?.message || "Cancellation failed.");
    }
  }

  /* ==========================================================
     CASH
  ========================================================== */

  async function cashOperation() {
    if (accountId === null) {
      setError("Select an account.");
      return;
    }

    const amount = Number(cashAmount);

    if (!amount || amount <= 0) {
      setError("Enter a valid amount.");
      return;
    }

    setCashLoading(true);
    setError("");

    try {
      await apiFetch(`/account/${accountId}/${cashAction}`, {
        method: "POST",
        body: JSON.stringify({
          amount,
        }),
      });

      setCashAmount("");

      setMessage(
        cashAction === "deposit"
          ? "Cash deposited successfully."
          : "Cash withdrawn successfully.",
      );

      await refresh();
    } catch (error: any) {
      setError(error?.message || "Cash operation failed.");
    } finally {
      setCashLoading(false);
    }
  }

  /* ==========================================================
     CREATE ACCOUNT
  ========================================================== */

  async function createAccount() {
    const cash = Number(initialCash);

    if (cash < 0 || Number.isNaN(cash)) {
      setError("Enter valid initial cash.");
      return;
    }

    setAccountLoading(true);

    setError("");

    try {
      const data = await apiFetch("/accounts", {
        method: "POST",
        body: JSON.stringify({
          initial_cash: cash,
        }),
      });

      const id = data.account?.account_id;

      if (id !== undefined) {
        setAccountId(Number(id));
      }

      setMessage(`Account #${id} created.`);

      setInitialCash("1000000");

      await fetchAccounts();
    } catch (error: any) {
      setError(error?.message || "Account creation failed.");
    } finally {
      setAccountLoading(false);
    }
  }

  /* ==========================================================
     LOGOUT
  ========================================================== */

  function logout() {
    localStorage.removeItem(TOKEN_KEY);

    setUser(null);
    setAccounts([]);
    setAccount(null);
    setPortfolio(null);
    setOrders([]);
    setTrades([]);
    setExecutions([]);
    setBids([]);
    setAsks([]);
  }

  /* ==========================================================
     BOOT
  ========================================================== */

  if (booting) {
    return (
      <main className="min-h-screen bg-[#070b12] text-white flex items-center justify-center">
        <div className="text-gray-500">Connecting to exchange...</div>
      </main>
    );
  }

  if (!user) {
    return <AuthScreen onAuthenticated={setUser} />;
  }

  /* ==========================================================
     ACTIVE ORDERS
  ========================================================== */

  const activeOrders = orders.filter(
    (order) => order.status === "OPEN" || order.status === "PARTIALLY_FILLED",
  );

  /* ==========================================================
     UI
  ========================================================== */

  return (
    <main className="min-h-screen bg-[#070b12] text-white">
      {/* HEADER */}

      <header className="sticky top-0 z-30 border-b border-[#202a39] bg-[#080d15]/95 backdrop-blur">
        <div className="max-w-[1600px] mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-blue-600 flex items-center justify-center font-bold">
              LX
            </div>

            <div>
              <div className="font-bold">Low Latency Exchange</div>

              <div className="text-xs text-gray-500">
                Professional Trading Terminal
              </div>
            </div>
          </div>

          <div className="flex items-center gap-5">
            <div className="flex items-center gap-2 text-xs">
              <span
                className={`h-2.5 w-2.5 rounded-full ${
                  connected ? "bg-green-400" : "bg-red-400"
                }`}
              />
              API {connected ? "Connected" : "Offline"}
            </div>

            <div className="flex items-center gap-2 text-xs">
              <span
                className={`h-2.5 w-2.5 rounded-full ${
                  wsConnected ? "bg-green-400" : "bg-red-400"
                }`}
              />
              WS {wsConnected ? "Live" : "Offline"}
            </div>

            <div className="text-sm text-gray-400">{user.username}</div>

            <button
              onClick={logout}
              className="rounded-lg border border-[#29364a] px-4 py-2 text-sm hover:bg-[#111a27]"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-[1600px] mx-auto px-6 py-6">
        {/* ALERTS */}

        {error && (
          <div className="mb-5 rounded-xl border border-red-800 bg-red-950/40 px-5 py-4 text-red-300">
            {error}
          </div>
        )}

        {message && (
          <div className="mb-5 rounded-xl border border-green-800 bg-green-950/30 px-5 py-4 text-green-300">
            {message}
          </div>
        )}

        {/* ACCOUNT BAR */}

        <div className="rounded-xl border border-[#222d3d] bg-[#0d131d] p-4 mb-6 flex flex-wrap items-center gap-5">
          <div>
            <div className="text-xs text-gray-500 mb-1">Trading Account</div>

            <select
              value={accountId ?? ""}
              onChange={(event) => setAccountId(Number(event.target.value))}
              className="rounded-lg border border-[#29364a] bg-[#080d15] px-4 py-2 outline-none"
            >
              {accounts.map((item) => (
                <option key={item.account_id} value={item.account_id}>
                  Account #{item.account_id}
                </option>
              ))}
            </select>
          </div>

          <div className="h-9 w-px bg-[#253044]" />

          <div>
            <div className="text-xs text-gray-500">Available Cash</div>

            <div className="font-semibold">
              ${money(account?.available_cash)}
            </div>
          </div>

          <div>
            <div className="text-xs text-gray-500">Reserved Cash</div>

            <div className="font-semibold">
              ${money(account?.reserved_cash)}
            </div>
          </div>

          <div className="ml-auto flex items-end gap-2">
            <input
              type="number"
              value={initialCash}
              onChange={(event) => setInitialCash(event.target.value)}
              className="w-36 rounded-lg border border-[#29364a] bg-[#080d15] px-3 py-2"
              placeholder="Initial cash"
            />

            <button
              onClick={createAccount}
              disabled={accountLoading}
              className="rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 px-4 py-2"
            >
              + Account
            </button>
          </div>
        </div>

        {/* MARKET HEADER */}

        <div className="flex justify-between items-end mb-6">
          <div>
            <div className="text-xs text-gray-500 mb-1">Spot Market</div>

            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold">{SYMBOL}</h1>

              <span className="rounded-md border border-green-900 bg-green-950/40 px-2 py-1 text-xs text-green-400">
                LIVE
              </span>
            </div>
          </div>

          <div className="text-right">
            <div className="text-xs text-gray-500">Last Price</div>

            <div className="text-3xl font-bold">${money(marketPrice)}</div>
          </div>
        </div>

        {/* MARKET STATS */}

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Stat title="Best Bid" value={`$${money(bestBid)}`} />

          <Stat title="Best Ask" value={`$${money(bestAsk)}`} />

          <Stat title="Bid Volume" value={quantity(bidVolume)} />

          <Stat title="Ask Volume" value={quantity(askVolume)} />
        </div>

        {/* MAIN */}

        <div className="grid grid-cols-1 xl:grid-cols-[1fr_380px] gap-6">
          <div className="space-y-6">
            {/* PRICE CHART */}

            <Section
              title="Price Chart"
              right={
                <span className="text-xs text-gray-500">
                  Real exchange trades
                </span>
              }
            >
              <div className="h-[380px]">
                {chartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient
                          id="price-fill"
                          x1="0"
                          y1="0"
                          x2="0"
                          y2="1"
                        >
                          <stop
                            offset="0%"
                            stopColor="#2563eb"
                            stopOpacity={0.45}
                          />

                          <stop
                            offset="100%"
                            stopColor="#2563eb"
                            stopOpacity={0}
                          />
                        </linearGradient>
                      </defs>

                      <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />

                      <XAxis
                        dataKey="time"
                        tick={{
                          fill: "#64748b",
                          fontSize: 11,
                        }}
                        minTickGap={35}
                      />

                      <YAxis
                        domain={["auto", "auto"]}
                        tick={{
                          fill: "#64748b",
                          fontSize: 11,
                        }}
                        width={80}
                      />

                      <Tooltip
                        contentStyle={{
                          background: "#0d131d",
                          border: "1px solid #29364a",
                          borderRadius: 8,
                        }}
                        formatter={(value: any) => [
                          `$${money(Number(value))}`,
                          "Price",
                        ]}
                      />

                      <Area
                        type="monotone"
                        dataKey="price"
                        stroke="#3b82f6"
                        fill="url(#price-fill)"
                        strokeWidth={2}
                        dot={false}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-gray-600">
                    No trades yet. Execute a trade to populate the chart.
                  </div>
                )}
              </div>
            </Section>

            {/* ORDER BOOK */}

            <Section
              title="Order Book"
              right={
                <span className="text-xs text-gray-500">
                  Price-Time Priority
                </span>
              }
            >
              <div className="grid grid-cols-2 gap-8">
                {/* BIDS */}

                <div>
                  <div className="grid grid-cols-2 text-xs text-gray-500 border-b border-[#202a39] pb-3">
                    <span>Bid Price</span>

                    <span className="text-right">Quantity</span>
                  </div>

                  <div className="mt-2">
                    {bids.slice(0, 15).map((level, index) => (
                      <div
                        key={`${level.price}-${index}`}
                        className="grid grid-cols-2 py-2 text-sm"
                      >
                        <span className="text-green-400">
                          ${money(level.price)}
                        </span>

                        <span className="text-right">
                          {quantity(level.quantity)}
                        </span>
                      </div>
                    ))}

                    {bids.length === 0 && (
                      <div className="py-8 text-center text-gray-600 text-sm">
                        No bids
                      </div>
                    )}
                  </div>
                </div>

                {/* ASKS */}

                <div>
                  <div className="grid grid-cols-2 text-xs text-gray-500 border-b border-[#202a39] pb-3">
                    <span>Ask Price</span>

                    <span className="text-right">Quantity</span>
                  </div>

                  <div className="mt-2">
                    {asks.slice(0, 15).map((level, index) => (
                      <div
                        key={`${level.price}-${index}`}
                        className="grid grid-cols-2 py-2 text-sm"
                      >
                        <span className="text-red-400">
                          ${money(level.price)}
                        </span>

                        <span className="text-right">
                          {quantity(level.quantity)}
                        </span>
                      </div>
                    ))}

                    {asks.length === 0 && (
                      <div className="py-8 text-center text-gray-600 text-sm">
                        No asks
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </Section>

            {/* RECENT TRADES */}

            <Section title="Recent Trades">
              <div className="grid grid-cols-3 text-xs text-gray-500 border-b border-[#202a39] pb-3">
                <span>Time</span>

                <span className="text-right">Price</span>

                <span className="text-right">Quantity</span>
              </div>

              <div className="max-h-[320px] overflow-auto">
                {trades
                  .slice()
                  .reverse()
                  .slice(0, 50)
                  .map((trade, index) => (
                    <div
                      key={`${trade.trade_id}-${index}`}
                      className="grid grid-cols-3 py-2 border-b border-[#151d29] text-sm"
                    >
                      <span className="text-gray-500">
                        {timeFromNs(trade.timestamp_ns)}
                      </span>

                      <span className="text-right">${money(trade.price)}</span>

                      <span className="text-right">
                        {quantity(trade.quantity)}
                      </span>
                    </div>
                  ))}

                {trades.length === 0 && (
                  <div className="py-10 text-center text-gray-600">
                    No trades yet.
                  </div>
                )}
              </div>
            </Section>
          </div>

          {/* RIGHT SIDE */}

          <div className="space-y-6">
            {/* ORDER ENTRY */}

            <Section title="Place Order">
              <form onSubmit={submitOrder} className="space-y-5">
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setSide("BUY")}
                    className={`py-3 rounded-lg font-semibold ${
                      side === "BUY"
                        ? "bg-green-600"
                        : "bg-[#141d2a] text-gray-400"
                    }`}
                  >
                    BUY
                  </button>

                  <button
                    type="button"
                    onClick={() => setSide("SELL")}
                    className={`py-3 rounded-lg font-semibold ${
                      side === "SELL"
                        ? "bg-red-600"
                        : "bg-[#141d2a] text-gray-400"
                    }`}
                  >
                    SELL
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setOrderType("LIMIT")}
                    className={`py-2 rounded-lg ${
                      orderType === "LIMIT"
                        ? "bg-blue-600"
                        : "bg-[#141d2a] text-gray-400"
                    }`}
                  >
                    Limit
                  </button>

                  <button
                    type="button"
                    onClick={() => setOrderType("MARKET")}
                    className={`py-2 rounded-lg ${
                      orderType === "MARKET"
                        ? "bg-blue-600"
                        : "bg-[#141d2a] text-gray-400"
                    }`}
                  >
                    Market
                  </button>
                </div>

                {orderType === "LIMIT" && (
                  <div>
                    <label className="text-xs text-gray-500">Limit Price</label>

                    <input
                      type="number"
                      step="1"
                      value={orderPrice}
                      onChange={(event) => setOrderPrice(event.target.value)}
                      className="mt-2 w-full rounded-lg border border-[#29364a] bg-[#080d15] px-3 py-3 outline-none focus:border-blue-500"
                      placeholder="100000"
                    />
                  </div>
                )}

                <div>
                  <label className="text-xs text-gray-500">Quantity</label>

                  <input
                    type="number"
                    step="1"
                    value={orderQuantity}
                    onChange={(event) => setOrderQuantity(event.target.value)}
                    className="mt-2 w-full rounded-lg border border-[#29364a] bg-[#080d15] px-3 py-3 outline-none focus:border-blue-500"
                    placeholder="1"
                  />
                </div>

                <div className="rounded-lg border border-[#202a39] bg-[#080d15] p-4 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Account</span>

                    <span>#{accountId ?? "--"}</span>
                  </div>

                  <div className="flex justify-between mt-2">
                    <span className="text-gray-500">Available</span>

                    <span>${money(account?.available_cash)}</span>
                  </div>
                </div>

                <button
                  disabled={loading}
                  className={`w-full py-4 rounded-lg font-bold disabled:opacity-50 ${
                    side === "BUY"
                      ? "bg-green-600 hover:bg-green-500"
                      : "bg-red-600 hover:bg-red-500"
                  }`}
                >
                  {loading ? "Submitting..." : `${side} ${orderType}`}
                </button>
              </form>
            </Section>

            {/* CASH MANAGEMENT */}

            <Section title="Cash Management">
              <div className="grid grid-cols-2 gap-2 mb-4">
                <button
                  onClick={() => setCashAction("deposit")}
                  className={`py-2 rounded-lg ${
                    cashAction === "deposit"
                      ? "bg-blue-600"
                      : "bg-[#141d2a] text-gray-400"
                  }`}
                >
                  Deposit
                </button>

                <button
                  onClick={() => setCashAction("withdraw")}
                  className={`py-2 rounded-lg ${
                    cashAction === "withdraw"
                      ? "bg-blue-600"
                      : "bg-[#141d2a] text-gray-400"
                  }`}
                >
                  Withdraw
                </button>
              </div>

              <input
                type="number"
                value={cashAmount}
                onChange={(event) => setCashAmount(event.target.value)}
                placeholder="Amount"
                className="w-full rounded-lg border border-[#29364a] bg-[#080d15] px-3 py-3 mb-3 outline-none"
              />

              <button
                onClick={cashOperation}
                disabled={cashLoading}
                className="w-full py-3 rounded-lg bg-[#182437] hover:bg-[#213149] disabled:opacity-50"
              >
                {cashLoading
                  ? "Processing..."
                  : cashAction === "deposit"
                    ? "Deposit Cash"
                    : "Withdraw Cash"}
              </button>
            </Section>
          </div>
        </div>

        {/* MY ORDERS */}

        <div className="mt-6">
          <Section
            title="My Orders"
            right={
              <span className="text-xs text-gray-500">
                {activeOrders.length} active
              </span>
            }
          >
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-500 border-b border-[#202a39]">
                    <th className="text-left py-3">ID</th>

                    <th className="text-left">Side</th>

                    <th className="text-left">Type</th>

                    <th className="text-right">Price</th>

                    <th className="text-right">Qty</th>

                    <th className="text-right">Filled</th>

                    <th className="text-right">Status</th>

                    <th />
                  </tr>
                </thead>

                <tbody>
                  {orders
                    .slice()
                    .reverse()
                    .map((order) => (
                      <tr
                        key={order.order_id}
                        className="border-b border-[#151d29]"
                      >
                        <td className="py-3">#{order.order_id}</td>

                        <td
                          className={
                            order.side === "BUY"
                              ? "text-green-400"
                              : "text-red-400"
                          }
                        >
                          {order.side}
                        </td>

                        <td>{order.order_type}</td>

                        <td className="text-right">
                          {order.order_type === "MARKET"
                            ? "Market"
                            : `$${money(order.price)}`}
                        </td>

                        <td className="text-right">
                          {quantity(order.quantity)}
                        </td>

                        <td className="text-right">
                          {quantity(order.filled_quantity)}
                        </td>

                        <td className="text-right">{order.status}</td>

                        <td className="text-right">
                          {(order.status === "OPEN" ||
                            order.status === "PARTIALLY_FILLED") && (
                            <button
                              onClick={() => cancelOrder(order)}
                              className="text-red-400 hover:text-red-300"
                            >
                              Cancel
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>

              {orders.length === 0 && (
                <div className="py-10 text-center text-gray-600">
                  No orders yet.
                </div>
              )}
            </div>
          </Section>
        </div>

        {/* LOWER DASHBOARD */}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          {/* EXECUTIONS */}

          <Section title="Execution History">
            <div className="space-y-2 max-h-[380px] overflow-auto">
              {executions
                .slice()
                .reverse()
                .map((execution, index) => (
                  <div
                    key={`${execution.trade_id}-${index}`}
                    className="rounded-lg border border-[#182233] bg-[#080d15] p-4"
                  >
                    <div className="flex justify-between">
                      <span
                        className={
                          execution.side === "BUY"
                            ? "text-green-400 font-semibold"
                            : "text-red-400 font-semibold"
                        }
                      >
                        {execution.side}
                      </span>

                      <span className="text-xs text-gray-500">
                        {timeFromNs(execution.timestamp_ns)}
                      </span>
                    </div>

                    <div className="grid grid-cols-3 gap-4 mt-4">
                      <div>
                        <div className="text-xs text-gray-600">Price</div>

                        <div>${money(execution.price)}</div>
                      </div>

                      <div>
                        <div className="text-xs text-gray-600">Quantity</div>

                        <div>{quantity(execution.quantity)}</div>
                      </div>

                      <div>
                        <div className="text-xs text-gray-600">Order</div>

                        <div>#{execution.order_id}</div>
                      </div>
                    </div>
                  </div>
                ))}

              {executions.length === 0 && (
                <div className="py-10 text-center text-gray-600">
                  No executions yet.
                </div>
              )}
            </div>
          </Section>

          {/* PORTFOLIO */}

          <Section title="Portfolio">
            <div className="grid grid-cols-2 gap-4 mb-5">
              <Stat title="Cash" value={`$${money(portfolio?.cash)}`} />

              <Stat
                title="Portfolio Value"
                value={`$${money(portfolio?.portfolio_value)}`}
              />

              <Stat
                title="Market Value"
                value={`$${money(portfolio?.market_value)}`}
              />

              <Stat
                title="Positions"
                value={String(portfolio?.positions?.length || 0)}
              />
            </div>

            <div className="rounded-lg border border-[#202a39] overflow-hidden">
              <div className="grid grid-cols-4 px-4 py-3 bg-[#080d15] text-xs text-gray-500">
                <span>Symbol</span>

                <span className="text-right">Qty</span>

                <span className="text-right">Price</span>

                <span className="text-right">Value</span>
              </div>

              {portfolio?.positions?.map((position) => (
                <div
                  key={position.symbol}
                  className="grid grid-cols-4 px-4 py-3 border-t border-[#182233]"
                >
                  <span className="font-medium">{position.symbol}</span>

                  <span className="text-right">
                    {quantity(position.quantity)}
                  </span>

                  <span className="text-right">
                    ${money(position.market_price)}
                  </span>

                  <span className="text-right">
                    ${money(position.market_value)}
                  </span>
                </div>
              ))}

              {(!portfolio || portfolio.positions.length === 0) && (
                <div className="py-8 text-center text-gray-600">
                  No positions.
                </div>
              )}
            </div>
          </Section>
        </div>

        {/* FOOTER */}

        <div className="py-8 flex justify-between text-xs text-gray-600">
          <span>Low Latency Exchange · {SYMBOL}</span>

          <span>
            {lastUpdate
              ? `Updated ${lastUpdate.toLocaleTimeString()}`
              : "Updating..."}
          </span>
        </div>
      </div>
    </main>
  );
}
