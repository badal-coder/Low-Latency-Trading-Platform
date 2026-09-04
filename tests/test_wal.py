from engine.wal import WriteAheadLog


def test_wal_appends_records(tmp_path):
    path = tmp_path / "exchange.wal"

    wal = WriteAheadLog(path, fsync=False)

    wal.append("event-1")
    wal.append("event-2")
    wal.append("event-3")

    wal.close()

    assert path.read_text(encoding="utf-8").splitlines() == [
        "event-1",
        "event-2",
        "event-3",
    ]


def test_wal_reads_records_in_order(tmp_path):
    path = tmp_path / "exchange.wal"

    wal = WriteAheadLog(path, fsync=False)

    wal.append("first")
    wal.append("second")

    wal.close()

    reader = WriteAheadLog(path, fsync=False)

    assert reader.read_all() == [
        "first",
        "second",
    ]

    reader.close()


def test_wal_creates_parent_directory(tmp_path):
    path = tmp_path / "logs" / "exchange.wal"

    wal = WriteAheadLog(path, fsync=False)

    wal.append("hello")
    wal.close()

    assert path.exists()


def test_wal_rejects_newline_records(tmp_path):
    path = tmp_path / "exchange.wal"

    wal = WriteAheadLog(path, fsync=False)

    try:
        wal.append("bad\nrecord")
    except ValueError as exc:
        assert "newline" in str(exc)
    else:
        raise AssertionError("expected ValueError")

    wal.close()


def test_wal_rejects_non_string_records(tmp_path):
    path = tmp_path / "exchange.wal"

    wal = WriteAheadLog(path, fsync=False)

    try:
        wal.append(123)
    except TypeError:
        pass
    else:
        raise AssertionError("expected TypeError")

    wal.close()


def test_empty_wal_returns_empty_list(tmp_path):
    path = tmp_path / "exchange.wal"

    wal = WriteAheadLog(path, fsync=False)

    assert wal.read_all() == []

    wal.close()