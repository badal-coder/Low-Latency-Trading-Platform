from __future__ import annotations

from dataclasses import dataclass

from .order import Order


@dataclass(slots=True)
class OrderNode:
    order: Order
    prev: OrderNode | None = None
    next: OrderNode | None = None


class OrderQueue:
    __slots__ = (
        "head",
        "tail",
        "size",
    )

    def __init__(self):
        self.head: OrderNode | None = None
        self.tail: OrderNode | None = None
        self.size = 0

    def append(self, order: Order) -> OrderNode:
        node = OrderNode(order)

        tail = self.tail

        if tail is None:
            self.head = node
            self.tail = node
        else:
            node.prev = tail
            tail.next = node
            self.tail = node

        self.size += 1

        return node

    def peek(self) -> OrderNode | None:
        return self.head

    def remove(self, node: OrderNode) -> None:
        previous = node.prev
        next_node = node.next

        if previous is None:
            self.head = next_node
        else:
            previous.next = next_node

        if next_node is None:
            self.tail = previous
        else:
            next_node.prev = previous

        node.prev = None
        node.next = None

        self.size -= 1

    def popleft(self) -> OrderNode | None:
        node = self.head

        if node is None:
            return None

        self.remove(node)

        return node

    def __len__(self) -> int:
        return self.size