import json

from engine.event_bus import EventBus
from engine.events import (
    EventType,
    OrderAcceptedEvent,
)
from engine.wal import WriteAheadLog
from engine.wal_event_writer import WALEventWriter


def test_event_is_written_to_wal(tmp_path):
    path = tmp_path / "exchange.wal"

    wal = WriteAheadLog(path, fsync=False)
    writer = WALEventWriter(wal)

    event = OrderAcceptedEvent(
        sequence=1,
        event_type=EventType.ORDER_ACCEPTED,
        timestamp_ns=123,
        order_id=100,
        symbol="BTCUSD",
    )

    writer.record(event)
    writer.close()

    records = path.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(records) == 1

    data = json.loads(records[0])

    assert data["sequence"] == 1
    assert data["event_type"] == "ORDER_ACCEPTED"
    assert data["order_id"] == 100
    assert data["symbol"] == "BTCUSD"


def test_event_bus_can_write_directly_to_wal(tmp_path):
    path = tmp_path / "exchange.wal"

    wal = WriteAheadLog(path, fsync=False)
    writer = WALEventWriter(wal)

    bus = EventBus()
    bus.subscribe(writer.record)

    bus.publish(
        OrderAcceptedEvent(
            sequence=1,
            event_type=EventType.ORDER_ACCEPTED,
            timestamp_ns=123,
            order_id=100,
            symbol="BTCUSD",
        )
    )

    writer.close()

    records = path.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(records) == 1


def test_multiple_events_are_written_in_order(tmp_path):
    path = tmp_path / "exchange.wal"

    wal = WriteAheadLog(path, fsync=False)
    writer = WALEventWriter(wal)

    for sequence in range(1, 4):
        writer.record(
            OrderAcceptedEvent(
                sequence=sequence,
                event_type=EventType.ORDER_ACCEPTED,
                timestamp_ns=sequence,
                order_id=sequence,
                symbol="BTCUSD",
            )
        )

    writer.close()

    records = path.read_text(
        encoding="utf-8"
    ).splitlines()

    sequences = [
        json.loads(record)["sequence"]
        for record in records
    ]

    assert sequences == [1, 2, 3]