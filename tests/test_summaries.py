"""Tests for summary/event table helpers (Step 3.2 loss events)."""

from __future__ import annotations

import pandas as pd
import pytest

from measurement_inspector.model.base_table import build_base_table
from measurement_inspector.model.counter_logic import apply_counter_derived_metrics
from measurement_inspector.model.derived_metrics import apply_timing_derived_metrics
from measurement_inspector.model.summaries import build_loss_event_table
from tests.synthetic_fixtures import build_synthetic_record


def _build_counter_enriched_table(records: list) -> pd.DataFrame:
    base = build_base_table(records)
    with_timing = apply_timing_derived_metrics(base)
    return apply_counter_derived_metrics(with_timing)


def test_build_loss_event_table_returns_empty_when_no_gaps() -> None:
    table = _build_counter_enriched_table(
        [
            build_synthetic_record(
                "stream-a", send_ts=1_000_000, recv_ts=1_100_000, counter=10, size_bytes=8
            ),
            build_synthetic_record(
                "stream-a", send_ts=1_100_000, recv_ts=1_200_000, counter=11, size_bytes=8
            ),
        ]
    )

    result = build_loss_event_table(table)

    assert result.empty
    assert result.columns.tolist() == [
        "stream_id",
        "topic",
        "prev_recv_ts",
        "curr_recv_ts",
        "prev_send_ts",
        "curr_send_ts",
        "prev_counter",
        "curr_counter",
        "lost_msgs",
        "recv_gap_s",
        "send_gap_s",
        "latency_before_s",
        "latency_after_s",
    ]


def test_build_loss_event_table_extracts_single_and_multiple_gap_events() -> None:
    table = _build_counter_enriched_table(
        [
            build_synthetic_record(
                "stream-a",
                send_ts=1_000_000,
                recv_ts=1_100_000,
                counter=10,
                size_bytes=8,
                topic="a/topic",
            ),
            build_synthetic_record(
                "stream-a",
                send_ts=1_100_000,
                recv_ts=1_200_000,
                counter=12,
                size_bytes=8,
                topic="a/topic",
            ),
            build_synthetic_record(
                "stream-a",
                send_ts=1_200_000,
                recv_ts=1_350_000,
                counter=15,
                size_bytes=8,
                topic="a/topic",
            ),
            build_synthetic_record(
                "stream-b",
                send_ts=2_000_000,
                recv_ts=2_100_000,
                counter=4,
                size_bytes=8,
                topic="b/topic",
            ),
            build_synthetic_record(
                "stream-b",
                send_ts=2_200_000,
                recv_ts=2_350_000,
                counter=5,
                size_bytes=8,
                topic="b/topic",
            ),
        ]
    )

    result = build_loss_event_table(table)

    assert result[["stream_id", "lost_msgs"]].to_dict("records") == [
        {"stream_id": "stream-a", "lost_msgs": 1},
        {"stream_id": "stream-a", "lost_msgs": 2},
    ]

    first = result.iloc[0]
    assert first["prev_recv_ts"] == 1_100_000
    assert first["curr_recv_ts"] == 1_200_000
    assert first["prev_counter"] == 10
    assert first["curr_counter"] == 12
    assert first["recv_gap_s"] == 0.1
    assert first["send_gap_s"] == 0.1


def test_build_loss_event_table_carries_prev_curr_latency_columns() -> None:
    table = _build_counter_enriched_table(
        [
            build_synthetic_record(
                "stream-a", send_ts=1_000_000, recv_ts=1_200_000, counter=1, size_bytes=8
            ),
            build_synthetic_record(
                "stream-a", send_ts=1_120_000, recv_ts=1_400_000, counter=4, size_bytes=8
            ),
        ]
    )

    result = build_loss_event_table(table)

    assert result["latency_before_s"].tolist() == pytest.approx([0.2])
    assert result["latency_after_s"].tolist() == pytest.approx([0.28])
