import json
from dataclasses import asdict
from enum import Enum

from .events import Event


class EventRecorder:
    def __init__(self, path: str):
        self.path = path

    def record(self, event: Event) -> None:
        data = asdict(event)

        # Convert Enum values into stable string values so the
        # event can be serialized to JSON.
        for key, value in list(data.items()):
            if isinstance(value, Enum):
                data[key] = value.name

        # Keep the top-level event type explicit and stable.
        data["event_type"] = event.event_type.name

        with open(
            self.path,
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(
                    data,
                    separators=(",", ":"),
                )
                + "\n"
            )