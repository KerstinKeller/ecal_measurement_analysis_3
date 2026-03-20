"""Summary and event-table helpers for canonical analysis tables."""

from __future__ import annotations

import pandas as pd

_LOSS_EVENT_COLUMNS: list[str] = [
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


def _empty_loss_event_table() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "stream_id": pd.Series(dtype="string"),
            "topic": pd.Series(dtype="string"),
            "prev_recv_ts": pd.Series(dtype="Int64"),
            "curr_recv_ts": pd.Series(dtype="Int64"),
            "prev_send_ts": pd.Series(dtype="Int64"),
            "curr_send_ts": pd.Series(dtype="Int64"),
            "prev_counter": pd.Series(dtype="Int64"),
            "curr_counter": pd.Series(dtype="Int64"),
            "lost_msgs": pd.Series(dtype="Int64"),
            "recv_gap_s": pd.Series(dtype="Float64"),
            "send_gap_s": pd.Series(dtype="Float64"),
            "latency_before_s": pd.Series(dtype="Float64"),
            "latency_after_s": pd.Series(dtype="Float64"),
        }
    )[_LOSS_EVENT_COLUMNS]


def build_loss_event_table(base_table: pd.DataFrame) -> pd.DataFrame:
    """Build one row per inferred counter gap event from the canonical base table."""
    if base_table.empty:
        return _empty_loss_event_table()

    prev_recv_ts = base_table.groupby("stream_id", sort=False, dropna=False)["recv_ts"].shift(1)
    prev_send_ts = base_table.groupby("stream_id", sort=False, dropna=False)["send_ts"].shift(1)
    prev_counter = base_table.groupby("stream_id", sort=False, dropna=False)["counter"].shift(1)
    prev_latency_s = base_table.groupby("stream_id", sort=False, dropna=False)["latency_s"].shift(1)

    events = pd.DataFrame(
        {
            "stream_id": base_table["stream_id"],
            "topic": base_table["topic"],
            "prev_recv_ts": prev_recv_ts,
            "curr_recv_ts": base_table["recv_ts"],
            "prev_send_ts": prev_send_ts,
            "curr_send_ts": base_table["send_ts"],
            "prev_counter": prev_counter,
            "curr_counter": base_table["counter"],
            "lost_msgs": base_table["lost_msgs"],
            "recv_gap_s": base_table["recv_dt_s"],
            "send_gap_s": base_table["send_dt_s"],
            "latency_before_s": prev_latency_s,
            "latency_after_s": base_table["latency_s"],
        }
    )

    gap_mask = base_table["is_gap"].fillna(False)
    events = events[gap_mask].reset_index(drop=True)

    if events.empty:
        return _empty_loss_event_table()

    events["stream_id"] = events["stream_id"].astype("string")
    events["topic"] = events["topic"].astype("string")

    int_cols = [
        "prev_recv_ts",
        "curr_recv_ts",
        "prev_send_ts",
        "curr_send_ts",
        "prev_counter",
        "curr_counter",
        "lost_msgs",
    ]
    for col in int_cols:
        events[col] = events[col].astype("Int64")

    float_cols = ["recv_gap_s", "send_gap_s", "latency_before_s", "latency_after_s"]
    for col in float_cols:
        events[col] = events[col].astype("Float64")

    return events[_LOSS_EVENT_COLUMNS]
