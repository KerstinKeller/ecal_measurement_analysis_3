"""Tests for timing-derived metric computation (Step 2.2)."""

from __future__ import annotations

import pandas as pd
import pytest

from measurement_inspector.model.base_table import build_base_table
from measurement_inspector.model.derived_metrics import apply_timing_derived_metrics
from tests.synthetic_fixtures import build_synthetic_record


def test_apply_timing_derived_metrics_computes_latency_seconds() -> None:
    """Latency should be recv_ts - send_ts converted from microseconds to seconds."""
    base = build_base_table(
        [
            build_synthetic_record(
                "stream-1", send_ts=1_000_000, recv_ts=1_250_000, counter=1, size_bytes=64
            ),
            build_synthetic_record(
                "stream-1", send_ts=2_000_000, recv_ts=2_300_000, counter=2, size_bytes=64
            ),
        ]
    )

    result = apply_timing_derived_metrics(base)

    assert result["latency_s"].tolist() == pytest.approx([0.25, 0.3])


def test_apply_timing_derived_metrics_computes_send_and_recv_deltas_per_stream() -> None:
    """Inter-message deltas should be computed independently for each stream."""
    base = build_base_table(
        [
            build_synthetic_record(
                "stream-a", send_ts=1_000_000, recv_ts=1_100_000, counter=1, size_bytes=64
            ),
            build_synthetic_record(
                "stream-a", send_ts=1_300_000, recv_ts=1_450_000, counter=2, size_bytes=64
            ),
            build_synthetic_record(
                "stream-b", send_ts=2_000_000, recv_ts=2_100_000, counter=1, size_bytes=32
            ),
            build_synthetic_record(
                "stream-b", send_ts=2_500_000, recv_ts=2_750_000, counter=2, size_bytes=32
            ),
        ]
    )

    result = apply_timing_derived_metrics(base)

    stream_a = result[result["stream_id"] == "stream-a"].reset_index(drop=True)
    stream_b = result[result["stream_id"] == "stream-b"].reset_index(drop=True)

    assert pd.isna(stream_a.at[0, "send_dt_s"])
    assert pd.isna(stream_a.at[0, "recv_dt_s"])
    assert stream_a.at[1, "send_dt_s"] == 0.3
    assert stream_a.at[1, "recv_dt_s"] == 0.35

    assert pd.isna(stream_b.at[0, "send_dt_s"])
    assert pd.isna(stream_b.at[0, "recv_dt_s"])
    assert stream_b.at[1, "send_dt_s"] == 0.5
    assert stream_b.at[1, "recv_dt_s"] == 0.65


def test_apply_timing_derived_metrics_flags_send_time_nonmonotonic_rows() -> None:
    """Rows where send_dt_s is negative should be flagged as non-monotonic."""
    base = build_base_table(
        [
            build_synthetic_record(
                "stream-1", send_ts=1_000_000, recv_ts=1_100_000, counter=1, size_bytes=16
            ),
            build_synthetic_record(
                "stream-1", send_ts=900_000, recv_ts=1_200_000, counter=2, size_bytes=16
            ),
        ]
    )

    result = apply_timing_derived_metrics(base)

    assert pd.isna(result.at[0, "is_send_time_nonmonotonic"])
    assert result.at[1, "is_send_time_nonmonotonic"]


def test_apply_timing_derived_metrics_flags_recv_time_nonmonotonic_rows() -> None:
    """Rows where recv_dt_s is negative should be flagged as non-monotonic."""
    unsorted = pd.DataFrame(
        {
            "stream_id": pd.Series(["stream-1", "stream-1"], dtype="string"),
            "topic": pd.Series(["cam", "cam"], dtype="string"),
            "send_ts": pd.Series([1_000_000, 2_000_000], dtype="Int64"),
            "recv_ts": pd.Series([2_000_000, 1_500_000], dtype="Int64"),
            "counter": pd.Series([1, 2], dtype="Int64"),
            "size_bytes": pd.Series([16, 16], dtype="Int64"),
            "latency_s": pd.Series([pd.NA, pd.NA], dtype="Float64"),
            "send_dt_s": pd.Series([pd.NA, pd.NA], dtype="Float64"),
            "recv_dt_s": pd.Series([pd.NA, pd.NA], dtype="Float64"),
            "counter_delta": pd.Series([pd.NA, pd.NA], dtype="Int64"),
            "lost_msgs": pd.Series([pd.NA, pd.NA], dtype="Int64"),
            "is_gap": pd.Series([pd.NA, pd.NA], dtype="boolean"),
            "send_freq_hz": pd.Series([pd.NA, pd.NA], dtype="Float64"),
            "recv_freq_hz": pd.Series([pd.NA, pd.NA], dtype="Float64"),
            "send_period_error_s": pd.Series([pd.NA, pd.NA], dtype="Float64"),
            "recv_period_error_s": pd.Series([pd.NA, pd.NA], dtype="Float64"),
            "send_bitrate_bps": pd.Series([pd.NA, pd.NA], dtype="Float64"),
            "recv_bitrate_bps": pd.Series([pd.NA, pd.NA], dtype="Float64"),
            "latency_diff_s": pd.Series([pd.NA, pd.NA], dtype="Float64"),
            "is_counter_nonmonotonic": pd.Series([pd.NA, pd.NA], dtype="boolean"),
            "is_send_time_nonmonotonic": pd.Series([pd.NA, pd.NA], dtype="boolean"),
            "is_recv_time_nonmonotonic": pd.Series([pd.NA, pd.NA], dtype="boolean"),
            "is_latency_anomaly": pd.Series([pd.NA, pd.NA], dtype="boolean"),
            "is_send_period_anomaly": pd.Series([pd.NA, pd.NA], dtype="boolean"),
            "is_recv_period_anomaly": pd.Series([pd.NA, pd.NA], dtype="boolean"),
        }
    )

    result = apply_timing_derived_metrics(unsorted)

    assert pd.isna(result.at[0, "is_recv_time_nonmonotonic"])
    assert result.at[1, "is_recv_time_nonmonotonic"]
