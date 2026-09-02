import json
from dataclasses import asdict

from .events import Event


class EventRecorder:
    def __init__(self, path: str):
        self.path = path

    def record(self, event: Event) -> None:
        data = asdict(event)

        data["event_type"] = event.event_type.name

        with open(self.path, "a", encoding="utf-8") as file:
            file.write(
                json.dumps(data, separators=(",", ":"))
                + "\n"
            )