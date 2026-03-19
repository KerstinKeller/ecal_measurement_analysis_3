"""Tests for counter delta and gap inference logic (Step 3.1)."""

from __future__ import annotations

import pandas as pd

from measurement_inspector.config.schema import AnalysisConfig
from measurement_inspector.model.base_table import build_base_table
from measurement_inspector.model.counter_logic import apply_counter_derived_metrics
from tests.synthetic_fixtures import build_synthetic_record


def _build_base_with_counters(counters: list[int], stream_id: str = "stream-1") -> pd.DataFrame:
    records = [
        build_synthetic_record(
            stream_id=stream_id,
            topic="topic/a",
            send_ts=1_000_000 + index * 100_000,
            recv_ts=1_100_000 + index * 100_000,
            counter=counter,
            size_bytes=32,
        )
        for index, counter in enumerate(counters)
    ]
    return build_base_table(records)


def test_apply_counter_derived_metrics_no_loss_sequence() -> None:
    base = _build_base_with_counters([10, 11, 12])

    result = apply_counter_derived_metrics(base)

    assert result["counter_delta"].tolist() == [pd.NA, 1, 1]
    assert result["lost_msgs"].tolist() == [pd.NA, 0, 0]
    assert result["is_gap"].tolist() == [pd.NA, False, False]
    assert result["is_counter_nonmonotonic"].tolist() == [pd.NA, False, False]


def test_apply_counter_derived_metrics_single_loss_sequence() -> None:
    base = _build_base_with_counters([100, 102])

    result = apply_counter_derived_metrics(base)

    assert result["counter_delta"].tolist() == [pd.NA, 2]
    assert result["lost_msgs"].tolist() == [pd.NA, 1]
    assert result["is_gap"].tolist() == [pd.NA, True]
    assert result["is_counter_nonmonotonic"].tolist() == [pd.NA, False]


def test_apply_counter_derived_metrics_multi_loss_sequence() -> None:
    base = _build_base_with_counters([40, 44])

    result = apply_counter_derived_metrics(base)

    assert result["counter_delta"].tolist() == [pd.NA, 4]
    assert result["lost_msgs"].tolist() == [pd.NA, 3]
    assert result["is_gap"].tolist() == [pd.NA, True]


def test_apply_counter_derived_metrics_duplicate_counter_flags_nonmonotonic() -> None:
    base = _build_base_with_counters([7, 7, 8])

    result = apply_counter_derived_metrics(base)

    assert result["counter_delta"].tolist() == [pd.NA, 0, 1]
    assert result["lost_msgs"].tolist() == [pd.NA, 0, 0]
    assert result["is_gap"].tolist() == [pd.NA, False, False]
    assert result["is_counter_nonmonotonic"].tolist() == [pd.NA, True, False]


def test_apply_counter_derived_metrics_backward_jump_flags_nonmonotonic() -> None:
    base = _build_base_with_counters([15, 13, 14])

    result = apply_counter_derived_metrics(base)

    assert result["counter_delta"].tolist() == [pd.NA, -2, 1]
    assert result["lost_msgs"].tolist() == [pd.NA, 0, 0]
    assert result["is_gap"].tolist() == [pd.NA, False, False]
    assert result["is_counter_nonmonotonic"].tolist() == [pd.NA, True, False]


def test_apply_counter_derived_metrics_wrap_uses_configured_modulus() -> None:
    base = _build_base_with_counters([255, 2])

    result = apply_counter_derived_metrics(
        base,
        AnalysisConfig(counter_bits=8, counter_wrap=True),
    )

    assert result["counter_delta"].tolist() == [pd.NA, 3]
    assert result["lost_msgs"].tolist() == [pd.NA, 2]
    assert result["is_gap"].tolist() == [pd.NA, True]
    assert result["is_counter_nonmonotonic"].tolist() == [pd.NA, False]


def test_apply_counter_derived_metrics_wrap_disabled_keeps_raw_delta() -> None:
    base = _build_base_with_counters([255, 2])

    result = apply_counter_derived_metrics(
        base,
        AnalysisConfig(counter_bits=8, counter_wrap=False),
    )

    assert result["counter_delta"].tolist() == [pd.NA, -253]
    assert result["lost_msgs"].tolist() == [pd.NA, 0]
    assert result["is_gap"].tolist() == [pd.NA, False]
    assert result["is_counter_nonmonotonic"].tolist() == [pd.NA, True]


def test_apply_counter_derived_metrics_first_row_is_null_per_stream() -> None:
    stream_a = _build_base_with_counters([1, 2], stream_id="stream-a")
    stream_b = _build_base_with_counters([50, 52], stream_id="stream-b")
    base = pd.concat([stream_a, stream_b], ignore_index=True)

    result = apply_counter_derived_metrics(base)

    grouped = result.groupby("stream_id", sort=False, dropna=False)
    first_rows = grouped.head(1)

    assert first_rows["counter_delta"].isna().all()
    assert first_rows["lost_msgs"].isna().all()
    assert first_rows["is_gap"].isna().all()
    assert first_rows["is_counter_nonmonotonic"].isna().all()
