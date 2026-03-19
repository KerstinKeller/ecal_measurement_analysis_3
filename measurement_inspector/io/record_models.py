"""Typed models for normalized raw message records."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NormalizedRawRecord:
    """One normalized observed message from a measurement stream."""

    stream_id: str
    send_ts: int
    recv_ts: int
    counter: int
    size_bytes: int
    topic: str | None = None

    def __post_init__(self) -> None:
        if not self.stream_id:
            raise ValueError("stream_id must be a non-empty string")

        if self.topic is not None and self.topic == "":
            raise ValueError("topic must be non-empty when provided")

        if isinstance(self.send_ts, bool) or isinstance(self.recv_ts, bool):
            raise TypeError("send_ts and recv_ts must be integer microseconds")

        if not isinstance(self.send_ts, int) or not isinstance(self.recv_ts, int):
            raise TypeError("send_ts and recv_ts must be integer microseconds")

        if isinstance(self.counter, bool) or not isinstance(self.counter, int):
            raise TypeError("counter must be an integer")

        if isinstance(self.size_bytes, bool) or not isinstance(self.size_bytes, int):
            raise TypeError("size_bytes must be an integer")

        if self.size_bytes < 0:
            raise ValueError("size_bytes must be >= 0")
