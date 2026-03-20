"""Derived metric transforms applied to the canonical base table."""

from __future__ import annotations

import pandas as pd

from measurement_inspector.config.schema import AnalysisConfig

_MICROSECONDS_PER_SECOND = 1_000_000.0


def _expected_period_seconds(config: AnalysisConfig | None) -> float | None:
    """Resolve expected period from config, preferring expected frequency."""
    if config is None:
        return None

    if config.expected_freq_hz is not None:
        return 1.0 / config.expected_freq_hz

    return config.expected_period_s


def _reciprocal_seconds(series: pd.Series) -> pd.Series:
    """Return reciprocal in Hz for positive second intervals, otherwise null."""
    values = series.astype("Float64")
    frequency = pd.Series(pd.NA, index=values.index, dtype="Float64")
    positive_mask = values > 0
    frequency.loc[positive_mask] = (1.0 / values.loc[positive_mask]).astype("Float64")
    return frequency


def apply_timing_derived_metrics(
    base_table: pd.DataFrame, config: AnalysisConfig | None = None
) -> pd.DataFrame:
    """Compute timing-derived columns and monotonicity flags per stream.

    Calculations are stream-local and preserve row order from ``base_table``.
    """
    result = base_table.copy()

    send_s = result["send_ts"].astype("Float64") / _MICROSECONDS_PER_SECOND
    recv_s = result["recv_ts"].astype("Float64") / _MICROSECONDS_PER_SECOND

    result["latency_s"] = (recv_s - send_s).astype("Float64")

    groupby_stream = result.groupby("stream_id", sort=False, dropna=False)

    result["send_dt_s"] = (
        groupby_stream["send_ts"].diff().astype("Float64") / _MICROSECONDS_PER_SECOND
    )
    result["recv_dt_s"] = (
        groupby_stream["recv_ts"].diff().astype("Float64") / _MICROSECONDS_PER_SECOND
    )

    send_nonmonotonic = result["send_dt_s"] < 0
    recv_nonmonotonic = result["recv_dt_s"] < 0

    result["is_send_time_nonmonotonic"] = send_nonmonotonic.astype("boolean")
    result.loc[result["send_dt_s"].isna(), "is_send_time_nonmonotonic"] = pd.NA

    result["is_recv_time_nonmonotonic"] = recv_nonmonotonic.astype("boolean")
    result.loc[result["recv_dt_s"].isna(), "is_recv_time_nonmonotonic"] = pd.NA

    result["send_freq_hz"] = _reciprocal_seconds(result["send_dt_s"])
    result["recv_freq_hz"] = _reciprocal_seconds(result["recv_dt_s"])

    expected_period_s = _expected_period_seconds(config)
    if expected_period_s is None:
        result["send_period_error_s"] = pd.Series(pd.NA, index=result.index, dtype="Float64")
        result["recv_period_error_s"] = pd.Series(pd.NA, index=result.index, dtype="Float64")
    else:
        result["send_period_error_s"] = (
            result["send_dt_s"].astype("Float64") - expected_period_s
        ).astype("Float64")
        result["recv_period_error_s"] = (
            result["recv_dt_s"].astype("Float64") - expected_period_s
        ).astype("Float64")

    return result
