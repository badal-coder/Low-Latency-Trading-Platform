from __future__ import annotations

import os
from pathlib import Path


class WriteAheadLog:
    """
    Append-only write-ahead log for exchange events.

    Each event is stored as one line of UTF-8 text.
    The log is flushed and optionally fsynced after every append
    so committed events survive process crashes.
    """

    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        fsync: bool = True,
    ) -> None:
        self.path = Path(path)
        self.fsync = fsync

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._file = self.path.open(
            "a",
            encoding="utf-8",
            buffering=1,
        )

    def append(self, data: str) -> None:
        """
        Append one record to the WAL.
        """

        if not isinstance(data, str):
            raise TypeError("WAL record must be a string")

        if "\n" in data:
            raise ValueError(
                "WAL record must not contain newline characters"
            )

        self._file.write(data)
        self._file.write("\n")
        self._file.flush()

        if self.fsync:
            os.fsync(self._file.fileno())

    def read_all(self) -> list[str]:
        """
        Read all WAL records in order.
        """

        if not self.path.exists():
            return []

        with self.path.open(
            "r",
            encoding="utf-8",
        ) as file:
            return [
                line.rstrip("\n")
                for line in file
            ]

    def __iter__(self):
        return iter(self.read_all())

    def close(self) -> None:
        if not self._file.closed:
            self._file.close()

    def flush(self) -> None:
        self._file.flush()

        if self.fsync:
            os.fsync(self._file.fileno())

    def __enter__(self) -> "WriteAheadLog":
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.close()