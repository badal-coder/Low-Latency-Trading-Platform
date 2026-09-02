from collections.abc import Callable

from engine.events import Event


EventHandler = Callable[[Event], None]


class EventBus:
    def __init__(self):
        self._handlers: list[EventHandler] = []

    def subscribe(self, handler: EventHandler) -> None:
        self._handlers.append(handler)

    def publish(self, event: Event) -> None:
        for handler in self._handlers:
            handler(event)