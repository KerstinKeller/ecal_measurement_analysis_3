"""Tests for canonical observed-message base table construction (Step 2.1)."""

from __future__ import annotations

import pandas as pd

from measurement_inspector.model.base_table import BASE_TABLE_COLUMNS, build_base_table
from tests.synthetic_fixtures import build_synthetic_record


def test_build_base_table_single_stream_sorted_by_default_analysis_order() -> None:
    """Single-stream rows should be sorted by receive time, then send/counter tie-breakers."""
    records = [
        build_synthetic_record(
            stream_id="stream-1",
            topic="camera/front",
            send_ts=3_000,
            recv_ts=1_200,
            counter=3,
            size_bytes=128,
        ),
        build_synthetic_record(
            stream_id="stream-1",
            topic="camera/front",
            send_ts=1_000,
            recv_ts=1_000,
            counter=1,
            size_bytes=128,
        ),
        build_synthetic_record(
            stream_id="stream-1",
            topic="camera/front",
            send_ts=2_000,
            recv_ts=1_100,
            counter=2,
            size_bytes=128,
        ),
    ]

    base = build_base_table(records)

    assert list(base["recv_ts"]) == [1_000, 1_100, 1_200]
    assert list(base["send_ts"]) == [1_000, 2_000, 3_000]
    assert list(base["counter"]) == [1, 2, 3]


def test_build_base_table_combines_multiple_streams_in_one_table() -> None:
    """All streams should be present in one canonical table keyed by stream_id."""
    records = [
        build_synthetic_record("stream-2", 100, 220, 10, 64, topic="imu/main"),
        build_synthetic_record("stream-1", 90, 210, 7, 256, topic="camera/front"),
        build_synthetic_record("stream-2", 110, 230, 11, 64, topic="imu/main"),
    ]

    base = build_base_table(records)

    assert list(base["stream_id"]) == ["stream-1", "stream-2", "stream-2"]
    assert base.groupby("stream_id").size().to_dict() == {"stream-1": 1, "stream-2": 2}


def test_build_base_table_uses_observed_message_only_semantics() -> None:
    """Counter gaps must not create synthetic rows in the canonical base table."""
    records = [
        build_synthetic_record("stream-1", 1_000, 1_100, 10, 50),
        build_synthetic_record("stream-1", 2_000, 2_100, 15, 50),
    ]

    base = build_base_table(records)

    assert len(base) == 2
    assert list(base["counter"]) == [10, 15]


def test_build_base_table_contains_required_columns_with_nullable_dtypes() -> None:
    """Canonical table should include raw + placeholder derived columns with stable dtypes."""
    base = build_base_table(
        [build_synthetic_record("stream-1", 1_000, 1_100, 1, 50, topic="camera/front")]
    )

    assert list(base.columns) == BASE_TABLE_COLUMNS

    assert str(base["send_ts"].dtype) == "Int64"
    assert str(base["recv_ts"].dtype) == "Int64"
    assert str(base["counter"].dtype) == "Int64"
    assert str(base["size_bytes"].dtype) == "Int64"

    numeric_placeholder_cols = [
        "latency_s",
        "send_dt_s",
        "recv_dt_s",
        "counter_delta",
        "lost_msgs",
        "send_freq_hz",
        "recv_freq_hz",
        "send_period_error_s",
        "recv_period_error_s",
        "send_bitrate_bps",
        "recv_bitrate_bps",
        "latency_diff_s",
    ]
    for col in numeric_placeholder_cols:
        assert pd.isna(base.at[0, col])

    bool_placeholder_cols = [
        "is_gap",
        "is_counter_nonmonotonic",
        "is_send_time_nonmonotonic",
        "is_recv_time_nonmonotonic",
        "is_latency_anomaly",
        "is_send_period_anomaly",
        "is_recv_period_anomaly",
    ]
    for col in bool_placeholder_cols:
        assert pd.isna(base.at[0, col])
