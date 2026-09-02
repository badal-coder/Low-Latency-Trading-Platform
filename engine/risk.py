from dataclasses import dataclass

from .order import Order


@dataclass(slots=True)
class RiskLimits:
    max_order_quantity: int = 1_000
    max_order_notional: int = 1_000_000


class RiskEngine:
    def __init__(self, limits: RiskLimits | None = None):
        self.limits = limits or RiskLimits()

    def check_order(self, order: Order) -> tuple[bool, str | None]:
        if order.quantity <= 0:
            return False, "INVALID_QUANTITY"

        if order.order_type.name == "LIMIT" and order.price <= 0:
            return False, "INVALID_PRICE"

        if order.quantity > self.limits.max_order_quantity:
            return False, "MAX_ORDER_QUANTITY"

        if order.order_type.name == "LIMIT":
            notional = order.price * order.quantity

            if notional > self.limits.max_order_notional:
                return False, "MAX_ORDER_NOTIONAL"

        return True, None