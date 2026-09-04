import json
from dataclasses import asdict
from enum import Enum

from .events import Event
from .wal import WriteAheadLog


class WALEventWriter:
    """
    EventBus handler that persists exchange events to a WAL.
    """

    def __init__(self, wal: WriteAheadLog):
        self.wal = wal

    def record(self, event: Event) -> None:
        data = asdict(event)

        # Convert Enum values into stable names for JSON.
        for key, value in data.items():
            if isinstance(value, Enum):
                data[key] = value.name

        self.wal.append(
            json.dumps(
                data,
                separators=(",", ":"),
                sort_keys=True,
            )
        )

    def close(self) -> None:
        self.wal.close()