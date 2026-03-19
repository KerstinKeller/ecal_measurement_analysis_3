"""Synthetic normalized-record fixtures used by tests."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from measurement_inspector.io.record_models import NormalizedRawRecord


class FakeMeasurementAdapter:
    """Minimal adapter implementation for test scenarios."""

    def __init__(self, records: Iterable[NormalizedRawRecord]) -> None:
        self._records = list(records)

    def list_streams(self, measurement_path: str) -> pd.DataFrame:
        """Summarize available stream/topic combinations in the fake dataset."""
        del measurement_path

        if not self._records:
            return pd.DataFrame(columns=["stream_id", "topic", "message_count"])

        rows = [
            {
                "stream_id": record.stream_id,
                "topic": record.topic,
                "message_count": 1,
            }
            for record in self._records
        ]
        stream_df = pd.DataFrame(rows)
        grouped = (
            stream_df.groupby(["stream_id", "topic"], dropna=False, as_index=False)
            .agg(message_count=("message_count", "sum"))
            .sort_values(["stream_id", "topic"], na_position="last")
            .reset_index(drop=True)
        )
        return grouped

    def iter_messages(
        self,
        measurement_path: str,
        stream_ids: list[str] | None = None,
        topics: list[str] | None = None,
    ) -> Iterable[NormalizedRawRecord]:
        """Yield records filtered by stream/topic lists when provided."""
        del measurement_path

        allowed_streams = set(stream_ids) if stream_ids is not None else None
        allowed_topics = set(topics) if topics is not None else None

        for record in self._records:
            if allowed_streams is not None and record.stream_id not in allowed_streams:
                continue
            if allowed_topics is not None and record.topic not in allowed_topics:
                continue
            yield record


def build_synthetic_record(
    stream_id: str,
    send_ts: int,
    recv_ts: int,
    counter: int,
    size_bytes: int,
    topic: str | None = None,
) -> NormalizedRawRecord:
    """Create one valid normalized record for tests."""
    return NormalizedRawRecord(
        stream_id=stream_id,
        topic=topic,
        send_ts=send_ts,
        recv_ts=recv_ts,
        counter=counter,
        size_bytes=size_bytes,
    )


def build_synthetic_stream(
    stream_id: str,
    start_send_ts: int,
    send_step_us: int,
    start_recv_ts: int,
    recv_step_us: int,
    start_counter: int,
    size_bytes: int,
    count: int,
    topic: str | None = None,
) -> list[NormalizedRawRecord]:
    """Create a sequential synthetic stream of normalized records."""
    if count < 0:
        raise ValueError("count must be >= 0")

    return [
        build_synthetic_record(
            stream_id=stream_id,
            topic=topic,
            send_ts=start_send_ts + (index * send_step_us),
            recv_ts=start_recv_ts + (index * recv_step_us),
            counter=start_counter + index,
            size_bytes=size_bytes,
        )
        for index in range(count)
    ]
