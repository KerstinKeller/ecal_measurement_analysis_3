"""Tests for adapter protocol and synthetic fixture helpers (Step 1.2)."""

from __future__ import annotations

from collections.abc import Iterable

from measurement_inspector.io.ecal_reader import MeasurementAdapter
from measurement_inspector.io.record_models import NormalizedRawRecord
from tests.synthetic_fixtures import (
    FakeMeasurementAdapter,
    build_synthetic_record,
    build_synthetic_stream,
)


def test_fake_adapter_satisfies_protocol_and_filters_messages() -> None:
    """Fake adapter should satisfy protocol behavior expected by downstream analysis."""
    records = [
        build_synthetic_record(
            stream_id="stream-1",
            topic="camera/front",
            send_ts=1_000_000,
            recv_ts=1_001_000,
            counter=1,
            size_bytes=256,
        ),
        build_synthetic_record(
            stream_id="stream-2",
            topic="imu/main",
            send_ts=1_010_000,
            recv_ts=1_010_800,
            counter=5,
            size_bytes=64,
        ),
    ]
    adapter = FakeMeasurementAdapter(records)

    assert isinstance(adapter, MeasurementAdapter)

    streams = adapter.list_streams("/tmp/meas")
    assert list(streams.columns) == ["stream_id", "topic", "message_count"]
    assert streams.to_dict(orient="records") == [
        {"stream_id": "stream-1", "topic": "camera/front", "message_count": 1},
        {"stream_id": "stream-2", "topic": "imu/main", "message_count": 1},
    ]

    stream_filtered = list(adapter.iter_messages("/tmp/meas", stream_ids=["stream-2"]))
    assert stream_filtered == [records[1]]

    topic_filtered = list(adapter.iter_messages("/tmp/meas", topics=["camera/front"]))
    assert topic_filtered == [records[0]]


def test_synthetic_fixture_helpers_build_valid_normalized_records() -> None:
    """Fixture builders should create valid normalized record sequences."""
    first = build_synthetic_record(
        stream_id="stream-a",
        send_ts=2_000_000,
        recv_ts=2_000_900,
        counter=10,
        size_bytes=512,
        topic="radar/main",
    )
    assert isinstance(first, NormalizedRawRecord)

    stream_records = build_synthetic_stream(
        stream_id="stream-a",
        topic="radar/main",
        start_send_ts=2_000_000,
        send_step_us=10_000,
        start_recv_ts=2_000_900,
        recv_step_us=10_500,
        start_counter=10,
        size_bytes=512,
        count=3,
    )

    assert isinstance(stream_records, list)
    assert len(stream_records) == 3
    assert all(isinstance(row, NormalizedRawRecord) for row in stream_records)
    assert stream_records[0].counter == 10
    assert stream_records[1].counter == 11
    assert stream_records[2].counter == 12
    assert [row.send_ts for row in stream_records] == [2_000_000, 2_010_000, 2_020_000]
    assert [row.recv_ts for row in stream_records] == [2_000_900, 2_011_400, 2_021_900]


def test_fake_adapter_iter_messages_returns_iterable_of_normalized_records() -> None:
    """iter_messages should provide an iterable of normalized records for pipeline consumers."""
    adapter = FakeMeasurementAdapter(
        build_synthetic_stream(
            stream_id="stream-1",
            start_send_ts=10,
            send_step_us=10,
            start_recv_ts=11,
            recv_step_us=10,
            start_counter=0,
            size_bytes=100,
            count=2,
        )
    )

    rows = adapter.iter_messages("/tmp/meas")
    assert isinstance(rows, Iterable)
    assert all(isinstance(row, NormalizedRawRecord) for row in rows)
    assert [row.counter for row in adapter.iter_messages("/tmp/meas")] == [0, 1]
