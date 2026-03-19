"""Derived metric transforms applied to the canonical base table."""

from __future__ import annotations

import pandas as pd

_MICROSECONDS_PER_SECOND = 1_000_000.0


def apply_timing_derived_metrics(base_table: pd.DataFrame) -> pd.DataFrame:
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

    return result
