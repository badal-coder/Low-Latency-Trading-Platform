from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from pathlib import Path
from typing import Any
from threading import Lock
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from .exchange import Exchange
from .gateway import OrderRequest
from .order import OrderType, Side


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "exchange.db"
JWT_SECRET_PATH = DATA_DIR / "jwt_secret"

SYMBOL = "BTC/USD"
MARKET_MAKER_ACCOUNT_ID = 900000001
MARKET_MAKER_INITIAL_CASH = 10_000_000_000_000
MARKET_MAKER_INITIAL_BTC = 1_000_000

market_maker_lock = Lock()
# Keep the core exchange fast. The API is only an adapter.
exchange = Exchange()

security = HTTPBearer(auto_error=False)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Low Latency Exchange API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DATABASE
# ============================================================

def db() -> sqlite3.Connection:
    connection = sqlite3.connect(
        DB_PATH,
        timeout=10,
        check_same_thread=False,
    )
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    connection = db()

    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS accounts (
                account_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                initial_cash INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS positions (
                account_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, symbol),
                FOREIGN KEY(account_id) REFERENCES accounts(account_id)
            );
            """
        )

        connection.commit()

    finally:
        connection.close()


init_db()


# ============================================================
# JWT-LIKE TOKEN
# ============================================================
#
# We intentionally keep this dependency-free.
# Token format:
#
#   base64url(user_id:expiry:signature)
#
# It is sufficient for local development.
# Before production deployment, use a proper JWT library
# and an external secret manager.
# ============================================================

def load_secret() -> str:
    if JWT_SECRET_PATH.exists():
        return JWT_SECRET_PATH.read_text().strip()

    secret = secrets.token_urlsafe(64)

    JWT_SECRET_PATH.write_text(secret)

    return secret


JWT_SECRET = load_secret()


def make_token(user_id: int) -> str:
    expiry = int(time.time()) + 60 * 60 * 24 * 7

    payload = f"{user_id}:{expiry}"

    signature = hmac.new(
        JWT_SECRET.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()

    raw = f"{payload}:{signature}"

    return raw.encode().hex()


def verify_token(token: str) -> int:
    try:
        raw = bytes.fromhex(token).decode()

        user_id_text, expiry_text, signature = raw.split(":", 2)

        user_id = int(user_id_text)
        expiry = int(expiry_text)

        payload = f"{user_id}:{expiry}"

        expected = hmac.new(
            JWT_SECRET.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected):
            raise ValueError("invalid signature")

        if expiry < int(time.time()):
            raise ValueError("expired token")

        return user_id

    except Exception as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session.",
        ) from exc


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> sqlite3.Row:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
        )

    user_id = verify_token(credentials.credentials)

    connection = db()

    try:
        user = connection.execute(
            """
            SELECT id, username, created_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

    finally:
        connection.close()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User no longer exists.",
        )

    return user


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password: str) -> str:
    salt = os.urandom(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        310_000,
    )

    return (
        salt.hex()
        + "$"
        + digest.hex()
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)

        salt = bytes.fromhex(salt_hex)

        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt,
            310_000,
        )

        return hmac.compare_digest(
            digest.hex(),
            digest_hex,
        )

    except Exception:
        return False


# ============================================================
# REQUEST MODELS
# ============================================================

class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=128)
    initial_cash: int = Field(default=1_000_000, ge=0)


class LoginRequest(BaseModel):
    username: str
    password: str


class AccountCreateRequest(BaseModel):
    initial_cash: int = Field(default=1_000_000, ge=0)


class CashRequest(BaseModel):
    amount: int = Field(gt=0)


class OrderCreateRequest(BaseModel):
    account_id: int
    symbol: str = SYMBOL
    side: str
    order_type: str
    quantity: int = Field(gt=0)
    price: int = Field(default=0, ge=0)


# ============================================================
# SERIALIZATION HELPERS
# ============================================================

def enum_name(value: Any) -> str:
    if value is None:
        return ""

    return getattr(value, "name", str(value))


def order_to_dict(order: Any) -> dict[str, Any]:
    return {
        "order_id": int(order.order_id),
        "account_id": int(order.account_id),
        "symbol": order.symbol,
        "side": enum_name(order.side),
        "order_type": enum_name(order.order_type),
        "price": int(order.price),
        "quantity": int(order.quantity),
        "filled_quantity": int(order.filled_quantity),
        "remaining_quantity": int(order.remaining_quantity),
        "status": enum_name(order.status),
        "timestamp_ns": int(order.timestamp_ns),
    }


def trade_to_dict(trade: Any) -> dict[str, Any]:
    result = {
        "trade_id": int(getattr(trade, "trade_id", 0)),
        "symbol": getattr(trade, "symbol", ""),
        "buy_order_id": int(
            getattr(trade, "buy_order_id", 0)
        ),
        "sell_order_id": int(
            getattr(trade, "sell_order_id", 0)
        ),
        "price": int(getattr(trade, "price", 0)),
        "quantity": int(getattr(trade, "quantity", 0)),
        "timestamp_ns": int(
            getattr(trade, "timestamp_ns", 0)
        ),
    }

    return result


def account_to_dict(account: Any) -> dict[str, Any]:
    positions = dict(
        getattr(account, "positions", {}) or {}
    )

    reserved_positions = dict(
        getattr(account, "reserved_positions", {}) or {}
    )

    cash = int(getattr(account, "cash", 0))
    available_cash = int(
        getattr(
            account,
            "available_cash",
            cash - int(getattr(account, "reserved_cash", 0)),
        )
    )

    reserved_cash = int(
        getattr(
            account,
            "reserved_cash",
            max(0, cash - available_cash),
        )
    )

    return {
        "account_id": int(account.account_id),
        "cash": cash,
        "available_cash": available_cash,
        "reserved_cash": reserved_cash,
        "positions": positions,
        "reserved_positions": reserved_positions,
    }


# ============================================================
# ACCOUNT HELPERS
# ============================================================

def get_owned_account(
    account_id: int,
    user: sqlite3.Row,
):
    connection = db()

    try:
        row = connection.execute(
            """
            SELECT account_id
            FROM accounts
            WHERE account_id = ?
              AND user_id = ?
            """,
            (account_id, int(user["id"])),
        ).fetchone()

    finally:
        connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found.",
        )

    try:
        return exchange.accounts.get_account(account_id)

    except Exception as exc:
        raise HTTPException(
            status_code=404,
            detail="Account is not loaded in exchange.",
        ) from exc


def account_exists_in_db(account_id: int) -> bool:
    connection = db()

    try:
        row = connection.execute(
            """
            SELECT account_id
            FROM accounts
            WHERE account_id = ?
            """,
            (account_id,),
        ).fetchone()

        return row is not None

    finally:
        connection.close()


def next_account_id() -> int:
    connection = db()

    try:
        row = connection.execute(
            """
            SELECT COALESCE(MAX(account_id), 0) + 1 AS next_id
            FROM accounts
            """
        ).fetchone()

        return int(row["next_id"])

    finally:
        connection.close()


# ============================================================
# ACCOUNT RESTORATION
# ============================================================

def restore_accounts() -> None:
    connection = db()

    try:
        rows = connection.execute(
            """
            SELECT account_id, initial_cash
            FROM accounts
            ORDER BY account_id
            """
        ).fetchall()

    finally:
        connection.close()

    for row in rows:
        account_id = int(row["account_id"])
        initial_cash = int(row["initial_cash"])

        try:
            exchange.accounts.get_account(account_id)
            continue
        except Exception:
            pass

        try:
            exchange.create_account(
                account_id=account_id,
                initial_cash=initial_cash,
            )

        except Exception:
            # If restoration fails, don't prevent API startup.
            # The account can be diagnosed through logs.
            pass


restore_accounts()


# ============================================================
# HEALTH
# ============================================================

@app.get("/")
def root():
    return {
        "name": "Low Latency Exchange API",
        "version": "1.0.0",
        "status": "online",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "exchange": "online",
        "timestamp_ns": time.perf_counter_ns(),
    }


# ============================================================
# AUTH
# ============================================================

@app.post("/auth/signup")
def signup(request: SignupRequest):
    username = request.username.strip()

    if len(username) < 3:
        raise HTTPException(
            status_code=400,
            detail="Username must contain at least 3 characters.",
        )

    connection = db()

    try:
        existing = connection.execute(
            """
            SELECT id
            FROM users
            WHERE lower(username) = lower(?)
            """,
            (username,),
        ).fetchone()

        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail="Username already exists.",
            )

        cursor = connection.execute(
            """
            INSERT INTO users(
                username,
                password_hash,
                created_at
            )
            VALUES (?, ?, ?)
            """,
            (
                username,
                hash_password(request.password),
                int(time.time()),
            ),
        )

        user_id = int(cursor.lastrowid)

        connection.commit()

    finally:
        connection.close()

    account_id = next_account_id()

    exchange.create_account(
        account_id=account_id,
        initial_cash=request.initial_cash,
    )

    connection = db()

    try:
        connection.execute(
            """
            INSERT INTO accounts(
                account_id,
                user_id,
                initial_cash,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                account_id,
                user_id,
                request.initial_cash,
                int(time.time()),
            ),
        )

        connection.commit()

    finally:
        connection.close()

    token = make_token(user_id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "username": username,
        },
        "account": account_to_dict(
            exchange.accounts.get_account(account_id)
        ),
    }


@app.post("/auth/login")
def login(request: LoginRequest):
    connection = db()

    try:
        user = connection.execute(
            """
            SELECT id, username, password_hash, created_at
            FROM users
            WHERE lower(username) = lower(?)
            """,
            (request.username.strip(),),
        ).fetchone()

    finally:
        connection.close()

    if user is None or not verify_password(
        request.password,
        user["password_hash"],
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
        )

    token = make_token(int(user["id"]))

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": int(user["id"]),
            "username": user["username"],
        },
    }


@app.get("/auth/me")
def me(user: sqlite3.Row = Depends(current_user)):
    return {
        "user": {
            "id": int(user["id"]),
            "username": user["username"],
        }
    }


# ============================================================
# ACCOUNTS
# ============================================================

@app.get("/accounts")
def list_accounts(
    user: sqlite3.Row = Depends(current_user),
):
    connection = db()

    try:
        rows = connection.execute(
            """
            SELECT account_id, initial_cash, created_at
            FROM accounts
            WHERE user_id = ?
            ORDER BY account_id
            """,
            (int(user["id"]),),
        ).fetchall()

    finally:
        connection.close()

    result = []

    for row in rows:
        try:
            account = exchange.accounts.get_account(
                int(row["account_id"])
            )

            result.append(
                account_to_dict(account)
            )

        except Exception:
            result.append(
                {
                    "account_id": int(row["account_id"]),
                    "cash": int(row["initial_cash"]),
                    "available_cash": int(row["initial_cash"]),
                    "reserved_cash": 0,
                    "positions": {},
                    "reserved_positions": {},
                }
            )

    return {
        "accounts": result
    }


@app.post("/accounts")
def create_account(
    request: AccountCreateRequest,
    user: sqlite3.Row = Depends(current_user),
):
    account_id = next_account_id()

    account = exchange.create_account(
        account_id=account_id,
        initial_cash=request.initial_cash,
    )

    connection = db()

    try:
        connection.execute(
            """
            INSERT INTO accounts(
                account_id,
                user_id,
                initial_cash,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                account_id,
                int(user["id"]),
                request.initial_cash,
                int(time.time()),
            ),
        )

        connection.commit()

    finally:
        connection.close()

    return {
        "account": account_to_dict(account)
    }


@app.get("/account/{account_id}")
def get_account(
    account_id: int,
    user: sqlite3.Row = Depends(current_user),
):
    account = get_owned_account(
        account_id,
        user,
    )

    return account_to_dict(account)


# ============================================================
# CASH
# ============================================================

@app.post("/account/{account_id}/deposit")
def deposit(
    account_id: int,
    request: CashRequest,
    user: sqlite3.Row = Depends(current_user),
):
    account = get_owned_account(
        account_id,
        user,
    )

    try:
        account.deposit(request.amount)

    except AttributeError:
        # Compatibility fallback for account implementations
        # exposing cash directly.
        account.cash += request.amount

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return account_to_dict(account)


@app.post("/account/{account_id}/withdraw")
def withdraw(
    account_id: int,
    request: CashRequest,
    user: sqlite3.Row = Depends(current_user),
):
    account = get_owned_account(
        account_id,
        user,
    )

    try:
        account.withdraw(request.amount)

    except AttributeError:
        available = int(
            getattr(
                account,
                "available_cash",
                account.cash,
            )
        )

        if request.amount > available:
            raise HTTPException(
                status_code=400,
                detail="Insufficient available cash.",
            )

        account.cash -= request.amount

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return account_to_dict(account)


# ============================================================
# PORTFOLIO
# ============================================================

@app.get("/portfolio/{account_id}")
def portfolio(
    account_id: int,
    user: sqlite3.Row = Depends(current_user),
):
    account = get_owned_account(
        account_id,
        user,
    )

    data = account_to_dict(account)

    positions = []

    for symbol, quantity in data["positions"].items():
        quantity = int(quantity)

        market_price = 0

        try:
            book = exchange.matching_engine.get_book(symbol)

            bid = book.best_bid()
            ask = book.best_ask()

            if bid is not None and ask is not None:
                market_price = (bid + ask) // 2
            elif bid is not None:
                market_price = bid
            elif ask is not None:
                market_price = ask

        except Exception:
            pass

        positions.append(
            {
                "symbol": symbol,
                "quantity": quantity,
                "market_price": market_price,
                "market_value": quantity * market_price,
            }
        )

    market_value = sum(
        int(position["market_value"])
        for position in positions
    )

    cash = int(data["cash"])

    portfolio_value = cash + market_value

    return {
        "account_id": account_id,
        "cash": cash,
        "available_cash": data["available_cash"],
        "reserved_cash": data["reserved_cash"],
        "market_value": market_value,
        "portfolio_value": portfolio_value,
        "equity": portfolio_value,
        "total_value": portfolio_value,
        "total_pnl": portfolio_value,
        "positions": positions,
    }


# ============================================================
# ORDER SUBMISSION
# ============================================================

def parse_side(value: str) -> Side:
    try:
        return Side[value.strip().upper()]
    except KeyError as exc:
        raise HTTPException(
            status_code=400,
            detail="side must be BUY or SELL.",
        ) from exc


def parse_order_type(value: str) -> OrderType:
    try:
        return OrderType[value.strip().upper()]
    except KeyError as exc:
        raise HTTPException(
            status_code=400,
            detail="order_type must be LIMIT or MARKET.",
        ) from exc


@app.post("/orders")
def submit_order(
    request: OrderCreateRequest,
    user: sqlite3.Row = Depends(current_user),
):
    if request.symbol != SYMBOL:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported symbol. Use {SYMBOL}.",
        )

    account = get_owned_account(
        request.account_id,
        user,
    )

    side = parse_side(request.side)
    order_type = parse_order_type(request.order_type)

    if request.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than zero.",
        )

    if (
        order_type == OrderType.LIMIT
        and request.price <= 0
    ):
        raise HTTPException(
            status_code=400,
            detail="Limit price must be greater than zero.",
        )

    order_id = time.time_ns()

    request_object = OrderRequest(
        order_id=order_id,
        account_id=request.account_id,
        symbol=request.symbol,
        side=side,
        order_type=order_type,
        quantity=request.quantity,
        price=request.price,
        timestamp_ns=time.perf_counter_ns(),
    )

    try:
        trades = exchange.submit_order(
            request_object
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    trade_dicts = [
        trade_to_dict(trade)
        for trade in trades
    ]

    # Store recent trade information in API memory.
    recent_trades.extend(trade_dicts)

    if len(recent_trades) > 500:
        del recent_trades[:-500]

    try:
        order = exchange.gateway.get_order(
            order_id
        )

        order_data = order_to_dict(order)

    except Exception:
        # Filled orders may no longer be present in
        # gateway.orders depending on the core lifecycle.
        order_data = {
            "order_id": order_id,
            "account_id": request.account_id,
            "symbol": request.symbol,
            "side": side.name,
            "order_type": order_type.name,
            "price": request.price,
            "quantity": request.quantity,
            "filled_quantity": request.quantity
            if trades
            else 0,
            "remaining_quantity": 0
            if trades
            else request.quantity,
            "status": "FILLED"
            if trades
            else "OPEN",
            "timestamp_ns": request_object.timestamp_ns,
        }

    return {
        "status": "accepted",
        "order": order_data,
        "order_id": order_id,
        "trades": len(trades),
        "executions": trade_dicts,
    }


# ============================================================
# ORDERS
# ============================================================

def all_exchange_orders() -> list[Any]:
    result = []

    gateway_orders = getattr(
        exchange.gateway,
        "orders",
        {},
    )

    result.extend(
        gateway_orders.values()
    )

    return result


@app.get("/orders")
def list_orders(
    user: sqlite3.Row = Depends(current_user),
):
    owned_ids = set()

    connection = db()

    try:
        rows = connection.execute(
            """
            SELECT account_id
            FROM accounts
            WHERE user_id = ?
            """,
            (int(user["id"]),),
        ).fetchall()

        owned_ids = {
            int(row["account_id"])
            for row in rows
        }

    finally:
        connection.close()

    result = []

    for order in all_exchange_orders():
        if int(order.account_id) in owned_ids:
            result.append(
                order_to_dict(order)
            )

    result.sort(
        key=lambda x: x["timestamp_ns"]
    )

    return {
        "orders": result
    }


@app.delete("/orders/{symbol:path}/{order_id}")
def cancel_order(
    symbol: str,
    order_id: int,
):
    try:
        order = exchange.gateway.get_order(
            order_id
        )

    except Exception as exc:
        raise HTTPException(
            status_code=404,
            detail="Order not found or already completed.",
        ) from exc

    get_owned_account(
        int(order.account_id),
        user,
    )

    try:
        result = exchange.cancel_order(
            symbol,
            order_id,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if not result:
        raise HTTPException(
            status_code=400,
            detail="Order could not be cancelled.",
        )

    return {
        "status": "cancelled",
        "order_id": order_id,
    }


# ============================================================
# ORDER BOOK
# ============================================================

@app.get("/orderbook/{symbol:path}")
def orderbook(
    symbol: str,
):
    if symbol != SYMBOL:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported symbol. Use {SYMBOL}.",
        )

    book = exchange.matching_engine.get_book(
        symbol
    )

    bids = []

    for price in sorted(
        book.bids.keys(),
        reverse=True,
    )[:25]:
        level = book.bids[price]

        quantity = 0

        node = level.orders.peek()

        while node is not None:
            quantity += int(
                node.order.remaining_quantity
            )
            break

        if quantity > 0:
            bids.append(
                {
                    "price": int(price),
                    "quantity": quantity,
                }
            )

    asks = []

    for price in sorted(
        book.asks.keys()
    )[:25]:
        level = book.asks[price]

        quantity = 0

        node = level.orders.peek()

        while node is not None:
            quantity += int(
                node.order.remaining_quantity
            )
            break

        if quantity > 0:
            asks.append(
                {
                    "price": int(price),
                    "quantity": quantity,
                }
            )

    return {
        "symbol": symbol,
        "bids": bids,
        "asks": asks,
    }


# ============================================================
# TRADES
# ============================================================

recent_trades: list[dict[str, Any]] = []


@app.get("/trades/{symbol:path}")
def trades(
    symbol: str,
):
    if symbol != SYMBOL:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported symbol. Use {SYMBOL}.",
        )

    return {
        "symbol": symbol,
        "trades": recent_trades[-500:],
    }


# ============================================================
# EXECUTIONS
# ============================================================

@app.get("/executions/{account_id}")
def executions(
    account_id: int,
    user: sqlite3.Row = Depends(current_user),
):
    get_owned_account(
        account_id,
        user,
    )

    result = []

    for trade in recent_trades:
        buy_id = int(
            trade.get("buy_order_id", 0)
        )

        sell_id = int(
            trade.get("sell_order_id", 0)
        )

        buy_order = exchange.gateway.orders.get(
            buy_id
        )

        sell_order = exchange.gateway.orders.get(
            sell_id
        )

        if buy_order is not None:
            if int(buy_order.account_id) == account_id:
                result.append(
                    {
                        "trade_id": trade.get("trade_id", 0),
                        "symbol": trade.get("symbol", SYMBOL),
                        "side": "BUY",
                        "order_id": buy_id,
                        "price": trade.get("price", 0),
                        "quantity": trade.get("quantity", 0),
                        "timestamp_ns": trade.get(
                            "timestamp_ns",
                            0,
                        ),
                    }
                )

        if sell_order is not None:
            if int(sell_order.account_id) == account_id:
                result.append(
                    {
                        "trade_id": trade.get("trade_id", 0),
                        "symbol": trade.get("symbol", SYMBOL),
                        "side": "SELL",
                        "order_id": sell_id,
                        "price": trade.get("price", 0),
                        "quantity": trade.get("quantity", 0),
                        "timestamp_ns": trade.get(
                            "timestamp_ns",
                            0,
                        ),
                    }
                )

    return {
        "executions": result
    }

# ============================================================
# MARKET MAKER / DEMO LIQUIDITY
# ============================================================

class LiquidityRequest(BaseModel):
    side: str
    price: int = Field(gt=0)
    quantity: int = Field(gt=0)


def get_or_create_market_maker():
    """
    Get the dedicated market-maker account and make sure
    it has enough BTC inventory for SELL liquidity.
    """

    try:
        account = exchange.accounts.get_account(
            MARKET_MAKER_ACCOUNT_ID
        )
    except Exception:
        account = exchange.create_account(
            account_id=MARKET_MAKER_ACCOUNT_ID,
            initial_cash=MARKET_MAKER_INITIAL_CASH,
        )

    # IMPORTANT:
    # Use Account.update_position() instead of directly
    # modifying account.positions.
    current_position = account.get_position(SYMBOL)

    if current_position < MARKET_MAKER_INITIAL_BTC:
        additional_btc = (
            MARKET_MAKER_INITIAL_BTC
            - current_position
        )

        account.update_position(
            SYMBOL,
            additional_btc,
        )

    return account


def submit_internal_liquidity(
    side: Side,
    price: int,
    quantity: int,
):
    get_or_create_market_maker()

    request = OrderRequest(
        order_id=time.time_ns(),
        account_id=MARKET_MAKER_ACCOUNT_ID,
        symbol=SYMBOL,
        side=side,
        order_type=OrderType.LIMIT,
        quantity=quantity,
        price=price,
        timestamp_ns=time.perf_counter_ns(),
    )

    return exchange.submit_order(request)


@app.post("/market-maker/liquidity")
def add_liquidity(
    request: LiquidityRequest,
    user: sqlite3.Row = Depends(current_user),
):
    side_name = request.side.strip().upper()

    if side_name not in {"BUY", "SELL"}:
        raise HTTPException(
            status_code=400,
            detail="Liquidity side must be BUY or SELL.",
        )

    if request.price <= 0:
        raise HTTPException(
            status_code=400,
            detail="Price must be greater than zero.",
        )

    if request.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than zero.",
        )

    with market_maker_lock:
        try:
            side = Side[side_name]

            trades = submit_internal_liquidity(
                side=side,
                price=request.price,
                quantity=request.quantity,
            )

            trade_dicts = [
                trade_to_dict(trade)
                for trade in trades
            ]

            recent_trades.extend(trade_dicts)

            if len(recent_trades) > 500:
                del recent_trades[:-500]

        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            ) from exc

    return {
        "status": "liquidity_added",
        "side": side_name,
        "symbol": SYMBOL,
        "price": request.price,
        "quantity": request.quantity,
        "trades": trade_dicts,
    }


@app.post("/market-maker/bootstrap")
def bootstrap_market(
    user: sqlite3.Row = Depends(current_user),
):
    """
    One-click market bootstrap.

    Creates several real resting orders around
    the current/default reference price.
    """

    get_or_create_market_maker()

    reference_price = 1938

    book = exchange.matching_engine.get_book(
        SYMBOL
    )

    best_bid = book.best_bid()
    best_ask = book.best_ask()

    if best_bid is not None:
        reference_price = int(best_bid)
    elif best_ask is not None:
        reference_price = int(best_ask)

    levels = [
        (
            Side.BUY,
            reference_price - 4,
            10,
        ),
        (
            Side.BUY,
            reference_price - 2,
            10,
        ),
        (
            Side.BUY,
            reference_price - 1,
            20,
        ),
        (
            Side.SELL,
            reference_price + 1,
            20,
        ),
        (
            Side.SELL,
            reference_price + 2,
            10,
        ),
        (
            Side.SELL,
            reference_price + 4,
            10,
        ),
    ]

    created = []

    with market_maker_lock:
        for side, price, quantity in levels:
            try:
                trades = submit_internal_liquidity(
                    side=side,
                    price=price,
                    quantity=quantity,
                )

                trade_dicts = [
                    trade_to_dict(trade)
                    for trade in trades
                ]

                recent_trades.extend(
                    trade_dicts
                )

                if len(recent_trades) > 500:
                    del recent_trades[:-500]

                created.append(
                    {
                        "side": side.name,
                        "price": price,
                        "quantity": quantity,
                        "trades": trade_dicts,
                    }
                )

            except Exception as exc:
                created.append(
                    {
                        "side": side.name,
                        "price": price,
                        "quantity": quantity,
                        "error": str(exc),
                    }
                )

    return {
        "status": "bootstrapped",
        "symbol": SYMBOL,
        "levels": created,
    }


@app.get("/market-maker/status")
def market_maker_status(
    user: sqlite3.Row = Depends(current_user),
):
    book = exchange.matching_engine.get_book(
        SYMBOL
    )

    return {
        "account_id": MARKET_MAKER_ACCOUNT_ID,
        "symbol": SYMBOL,
        "best_bid": book.best_bid(),
        "best_ask": book.best_ask(),
        "active_orders": len(
            getattr(book, "orders", {})
        ),
    }
# ============================================================
# WEBSOCKET
# ============================================================

websocket_clients: set[WebSocket] = set()


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
):
    await websocket.accept()

    websocket_clients.add(
        websocket
    )

    try:
        await websocket.send_json(
            {
                "type": "connected",
                "symbol": SYMBOL,
                "timestamp_ns": time.perf_counter_ns(),
            }
        )

        while True:
            message = await websocket.receive_text()

            if message.lower() == "ping":
                await websocket.send_json(
                    {
                        "type": "pong",
                        "timestamp_ns": time.perf_counter_ns(),
                    }
                )

    except WebSocketDisconnect:
        websocket_clients.discard(
            websocket
        )

    except Exception:
        websocket_clients.discard(
            websocket
        )


# ============================================================
# BROADCAST
# ============================================================

@app.get("/status")
def status(
    user: sqlite3.Row = Depends(current_user),
):
    gateway_orders = getattr(
        exchange.gateway,
        "orders",
        {},
    )

    return {
        "exchange": "online",
        "symbol": SYMBOL,
        "active_orders": len(gateway_orders),
        "accounts": len(
            getattr(
                exchange.accounts,
                "accounts",
                {},
            )
        ),
        "recent_trades": len(recent_trades),
        "timestamp_ns": time.perf_counter_ns(),
    }