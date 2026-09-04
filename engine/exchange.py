from __future__ import annotations

import time
from pathlib import Path

from .account import Account
from .account_manager import AccountManager
from .event_bus import EventBus
from .gateway import OrderGateway, OrderRequest
from .matching_engine import MatchingEngine, Trade
from .metrics import (
    active_orders,
    order_latency_seconds,
    orders_cancelled_total,
    orders_rejected_total,
    orders_total,
    trade_volume_total,
    trades_total,
)
from .order import OrderType, Side
from .settlement import SettlementEngine
from .wal import WriteAheadLog
from .wal_event_writer import WALEventWriter


class Exchange:
    def __init__(
        self,
        wal_path: str | Path | None = None,
        *,
        wal_fsync: bool = True,
    ):
        # ---------------------------------------------------------
        # Event infrastructure
        # ---------------------------------------------------------

        self.event_bus = EventBus()

        self.wal: WriteAheadLog | None = None
        self.wal_writer: WALEventWriter | None = None

        if wal_path is not None:
            self.wal = WriteAheadLog(
                wal_path,
                fsync=wal_fsync,
            )

            self.wal_writer = WALEventWriter(
                self.wal
            )

            self.event_bus.subscribe(
                self.wal_writer.record
            )

        # ---------------------------------------------------------
        # Matching engine
        # ---------------------------------------------------------

        self.matching_engine = MatchingEngine(
            event_bus=self.event_bus
        )

        self.gateway = OrderGateway(
            self.matching_engine
        )

        # Backwards-compatible alias.
        self.order_gateway = self.gateway

        # ---------------------------------------------------------
        # Accounts and settlement
        # ---------------------------------------------------------

        self.accounts = AccountManager()

        self.settlement = SettlementEngine()

        # ---------------------------------------------------------
        # Reservations
        # ---------------------------------------------------------

        # order_id -> reserved cash
        self.cash_reservations: dict[int, int] = {}

        # order_id -> (account_id, symbol, reserved quantity)
        self.position_reservations: dict[
            int,
            tuple[int, str, int],
        ] = {}

        # Initialize observable state.
        active_orders.set(0)

    # =============================================================
    # ACCOUNT MANAGEMENT
    # =============================================================

    def create_account(
        self,
        account_id: int,
        initial_cash: int,
    ) -> Account:

        return self.accounts.create_account(
            account_id,
            initial_cash,
        )

    # =============================================================
    # ORDER SUBMISSION
    # =============================================================

    def submit_order(
        self,
        request: OrderRequest,
    ) -> list[Trade]:

        start_ns = time.perf_counter_ns()

        orders_total.labels(
            side=request.side.name,
            order_type=request.order_type.name,
        ).inc()

        account = self.accounts.get_account(
            request.account_id
        )

        cash_reservation = 0
        position_reservation = 0

        # ---------------------------------------------------------
        # BUY LIMIT
        # ---------------------------------------------------------

        if (
            request.side == Side.BUY
            and request.order_type == OrderType.LIMIT
        ):
            cash_reservation = (
                request.price * request.quantity
            )

            account.reserve_cash(
                cash_reservation
            )

        # ---------------------------------------------------------
        # SELL
        # ---------------------------------------------------------

        elif request.side == Side.SELL:
            position_reservation = request.quantity

            account.reserve_position(
                request.symbol,
                position_reservation,
            )

        try:
            trades = self.gateway.submit(
                request
            )

            # -----------------------------------------------------
            # SETTLEMENT
            # -----------------------------------------------------

            for trade in trades:
                self._settle_trade(trade)

            order = self.gateway.get_order(
                request.order_id
            )

            # -----------------------------------------------------
            # BUY CASH RESERVATION
            # -----------------------------------------------------

            if cash_reservation > 0:

                remaining_value = (
                    order.remaining_quantity
                    * request.price
                )

                release = (
                    cash_reservation
                    - remaining_value
                )

                if release > 0:
                    account.release_cash(
                        release
                    )

                if remaining_value > 0:
                    self.cash_reservations[
                        request.order_id
                    ] = remaining_value

            # -----------------------------------------------------
            # SELL INVENTORY RESERVATION
            # -----------------------------------------------------

            if position_reservation > 0:

                remaining_quantity = (
                    order.remaining_quantity
                )

                if remaining_quantity > 0:

                    self.position_reservations[
                        request.order_id
                    ] = (
                        account.account_id,
                        request.symbol,
                        remaining_quantity,
                    )

                else:

                    self.position_reservations.pop(
                        request.order_id,
                        None,
                    )

            # -----------------------------------------------------
            # METRICS
            # -----------------------------------------------------

            elapsed_ns = (
                time.perf_counter_ns()
                - start_ns
            )

            order_latency_seconds.observe(
                elapsed_ns / 1_000_000_000
            )

            if trades:
                trades_total.inc(
                    len(trades)
                )

                for trade in trades:
                    trade_volume_total.inc(
                        trade.quantity
                    )

            active_orders.set(
                len(self.gateway.orders)
            )

            return trades

        except Exception:

            # Submission failed.
            # Release every reservation that was created.

            if cash_reservation > 0:
                account.release_cash(
                    cash_reservation
                )

            if position_reservation > 0:
                account.release_position(
                    request.symbol,
                    position_reservation,
                )

            orders_rejected_total.inc()

            raise

    # =============================================================
    # ORDER CANCELLATION
    # =============================================================

    def cancel_order(
        self,
        symbol: str,
        order_id: int,
    ) -> bool:

        order = self.gateway.get_order(
            order_id
        )

        result = self.gateway.cancel(
            symbol,
            order_id,
        )

        if not result:
            return False

        orders_cancelled_total.inc()

        # ---------------------------------------------------------
        # RELEASE BUY CASH
        # ---------------------------------------------------------

        reserved_cash = (
            self.cash_reservations.pop(
                order_id,
                0,
            )
        )

        if reserved_cash > 0:

            account = self.accounts.get_account(
                order.account_id
            )

            account.release_cash(
                reserved_cash
            )

        # ---------------------------------------------------------
        # RELEASE SELL INVENTORY
        # ---------------------------------------------------------

        position_reservation = (
            self.position_reservations.pop(
                order_id,
                None,
            )
        )

        if position_reservation is not None:

            (
                account_id,
                reserved_symbol,
                quantity,
            ) = position_reservation

            account = self.accounts.get_account(
                account_id
            )

            account.release_position(
                reserved_symbol,
                quantity,
            )

        # ---------------------------------------------------------
        # METRICS
        # ---------------------------------------------------------

        active_orders.set(
            len(self.gateway.orders)
        )

        return True

    # =============================================================
    # TRADE SETTLEMENT
    # =============================================================

    def _settle_trade(
        self,
        trade: Trade,
    ) -> None:

        buyer_order = self._find_order(
            trade.symbol,
            trade.buy_order_id,
        )

        seller_order = self._find_order(
            trade.symbol,
            trade.sell_order_id,
        )

        buyer = self.accounts.get_account(
            buyer_order.account_id
        )

        seller = self.accounts.get_account(
            seller_order.account_id
        )

        self.settlement.settle(
            trade,
            buyer,
            seller,
        )

        # ---------------------------------------------------------
        # BUY: CONSUME RESERVED CASH
        # ---------------------------------------------------------

        if buyer_order.side == Side.BUY:

            reserved = (
                self.cash_reservations.get(
                    buyer_order.order_id,
                    0,
                )
            )

            if reserved > 0:

                execution_value = (
                    trade.price
                    * trade.quantity
                )

                buyer.release_cash(
                    execution_value
                )

                remaining_reservation = (
                    reserved
                    - execution_value
                )

                if remaining_reservation > 0:

                    self.cash_reservations[
                        buyer_order.order_id
                    ] = remaining_reservation

                else:

                    self.cash_reservations.pop(
                        buyer_order.order_id,
                        None,
                    )

        # ---------------------------------------------------------
        # SELL: CONSUME RESERVED INVENTORY
        # ---------------------------------------------------------

        if seller_order.side == Side.SELL:

            reservation = (
                self.position_reservations.get(
                    seller_order.order_id
                )
            )

            if reservation is not None:

                (
                    account_id,
                    symbol,
                    reserved,
                ) = reservation

                remaining_reservation = (
                    reserved
                    - trade.quantity
                )

                seller.release_position(
                    symbol,
                    trade.quantity
                )

                if remaining_reservation > 0:

                    self.position_reservations[
                        seller_order.order_id
                    ] = (
                        account_id,
                        symbol,
                        remaining_reservation,
                    )

                else:

                    self.position_reservations.pop(
                        seller_order.order_id,
                        None,
                    )

    # =============================================================
    # ORDER LOOKUP
    # =============================================================

    def _find_order(
        self,
        symbol: str,
        order_id: int,
    ):
        order = self.gateway.orders.get(
            order_id
        )

        if order is not None:
            return order

        book = self.matching_engine.get_book(
            symbol
        )

        order = book.orders.get(
            order_id
        )

        if order is not None:
            return order

        raise ValueError(
            f"order {order_id} is no longer available"
        )

    # =============================================================
    # WAL MANAGEMENT
    # =============================================================

    def close(self) -> None:
        """
        Close the exchange's WAL resources.
        """

        if self.wal_writer is not None:
            self.wal_writer.close()

        elif self.wal is not None:
            self.wal.close()

    def flush(self) -> None:
        """
        Flush the WAL to disk.
        """

        if self.wal is not None:
            self.wal.flush()

    def __enter__(self) -> "Exchange":
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.close()