from engine.event_recorder import EventRecorder
from engine.events import (
    EventType,
    OrderAcceptedEvent,
)


def test_event_recorder_writes_event(tmp_path):
    path = tmp_path / "events.jsonl"

    recorder = EventRecorder(str(path))

    event = OrderAcceptedEvent(
        sequence=1,
        event_type=EventType.ORDER_ACCEPTED,
        timestamp_ns=123,
        order_id=100,
        symbol="BTCUSD",
    )

    recorder.record(event)

    lines = path.read_text().splitlines()

    assert len(lines) == 1

    assert '"sequence":1' in lines[0]
    assert '"event_type":"ORDER_ACCEPTED"' in lines[0]
    assert '"order_id":100' in lines[0]
    assert '"symbol":"BTCUSD"' in lines[0]


def test_event_recorder_appends_events(tmp_path):
    path = tmp_path / "events.jsonl"

    recorder = EventRecorder(str(path))

    for sequence in range(1, 4):
        recorder.record(
            OrderAcceptedEvent(
                sequence=sequence,
                event_type=EventType.ORDER_ACCEPTED,
                timestamp_ns=sequence,
                order_id=sequence,
                symbol="BTCUSD",
            )
        )

    lines = path.read_text().splitlines()

    assert len(lines) == 3