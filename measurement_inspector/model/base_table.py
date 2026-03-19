"""Canonical observed-message base table construction."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from measurement_inspector.io.record_models import NormalizedRawRecord

BASE_TABLE_COLUMNS: list[str] = [
    "stream_id",
    "topic",
    "send_ts",
    "recv_ts",
    "counter",
    "size_bytes",
    "latency_s",
    "send_dt_s",
    "recv_dt_s",
    "counter_delta",
    "lost_msgs",
    "is_gap",
    "send_freq_hz",
    "recv_freq_hz",
    "send_period_error_s",
    "recv_period_error_s",
    "send_bitrate_bps",
    "recv_bitrate_bps",
    "latency_diff_s",
    "is_counter_nonmonotonic",
    "is_send_time_nonmonotonic",
    "is_recv_time_nonmonotonic",
    "is_latency_anomaly",
    "is_send_period_anomaly",
    "is_recv_period_anomaly",
]

_SORT_COLUMNS = ["stream_id", "recv_ts", "send_ts", "counter", "size_bytes", "topic"]


def _empty_base_table() -> pd.DataFrame:
    """Return an empty canonical base table with stable nullable dtypes."""
    return pd.DataFrame(
        {
            "stream_id": pd.Series(dtype="string"),
            "topic": pd.Series(dtype="string"),
            "send_ts": pd.Series(dtype="Int64"),
            "recv_ts": pd.Series(dtype="Int64"),
            "counter": pd.Series(dtype="Int64"),
            "size_bytes": pd.Series(dtype="Int64"),
            "latency_s": pd.Series(dtype="Float64"),
            "send_dt_s": pd.Series(dtype="Float64"),
            "recv_dt_s": pd.Series(dtype="Float64"),
            "counter_delta": pd.Series(dtype="Int64"),
            "lost_msgs": pd.Series(dtype="Int64"),
            "is_gap": pd.Series(dtype="boolean"),
            "send_freq_hz": pd.Series(dtype="Float64"),
            "recv_freq_hz": pd.Series(dtype="Float64"),
            "send_period_error_s": pd.Series(dtype="Float64"),
            "recv_period_error_s": pd.Series(dtype="Float64"),
            "send_bitrate_bps": pd.Series(dtype="Float64"),
            "recv_bitrate_bps": pd.Series(dtype="Float64"),
            "latency_diff_s": pd.Series(dtype="Float64"),
            "is_counter_nonmonotonic": pd.Series(dtype="boolean"),
            "is_send_time_nonmonotonic": pd.Series(dtype="boolean"),
            "is_recv_time_nonmonotonic": pd.Series(dtype="boolean"),
            "is_latency_anomaly": pd.Series(dtype="boolean"),
            "is_send_period_anomaly": pd.Series(dtype="boolean"),
            "is_recv_period_anomaly": pd.Series(dtype="boolean"),
        }
    )[BASE_TABLE_COLUMNS]


def build_base_table(records: Iterable[NormalizedRawRecord]) -> pd.DataFrame:
    """Build a canonical one-row-per-observed-message table from normalized records."""
    rows = [
        {
            "stream_id": record.stream_id,
            "topic": record.topic,
            "send_ts": record.send_ts,
            "recv_ts": record.recv_ts,
            "counter": record.counter,
            "size_bytes": record.size_bytes,
        }
        for record in records
    ]

    if not rows:
        return _empty_base_table()

    base = pd.DataFrame(rows)
    base["stream_id"] = base["stream_id"].astype("string")
    base["topic"] = base["topic"].astype("string")
    base["send_ts"] = base["send_ts"].astype("Int64")
    base["recv_ts"] = base["recv_ts"].astype("Int64")
    base["counter"] = base["counter"].astype("Int64")
    base["size_bytes"] = base["size_bytes"].astype("Int64")

    base = base.sort_values(_SORT_COLUMNS, kind="mergesort").reset_index(drop=True)

    float_placeholders = [
        "latency_s",
        "send_dt_s",
        "recv_dt_s",
        "send_freq_hz",
        "recv_freq_hz",
        "send_period_error_s",
        "recv_period_error_s",
        "send_bitrate_bps",
        "recv_bitrate_bps",
        "latency_diff_s",
    ]
    int_placeholders = ["counter_delta", "lost_msgs"]
    bool_placeholders = [
        "is_gap",
        "is_counter_nonmonotonic",
        "is_send_time_nonmonotonic",
        "is_recv_time_nonmonotonic",
        "is_latency_anomaly",
        "is_send_period_anomaly",
        "is_recv_period_anomaly",
    ]

    for col in float_placeholders:
        base[col] = pd.Series(pd.NA, index=base.index, dtype="Float64")

    for col in int_placeholders:
        base[col] = pd.Series(pd.NA, index=base.index, dtype="Int64")

    for col in bool_placeholders:
        base[col] = pd.Series(pd.NA, index=base.index, dtype="boolean")

    return base[BASE_TABLE_COLUMNS]
