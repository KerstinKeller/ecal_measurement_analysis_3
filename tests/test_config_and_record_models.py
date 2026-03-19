"""Tests for step 1.1 config and normalized record schemas."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from measurement_inspector.config.defaults import default_analysis_config
from measurement_inspector.config.schema import AnalysisConfig
from measurement_inspector.io.record_models import NormalizedRawRecord


def test_default_analysis_config_values() -> None:
    """Default config should reflect documented baseline analysis semantics."""
    cfg = default_analysis_config()

    assert cfg.counter_bits == 16
    assert cfg.counter_wrap is True
    assert cfg.counter_modulus is None
    assert cfg.expected_period_s is None
    assert cfg.expected_freq_hz is None
    assert cfg.latency_warn_s is None
    assert cfg.period_error_warn_s is None
    assert cfg.bucket_size_s == 1.0
    assert cfg.max_raw_points_before_rasterize == 200_000
    assert cfg.default_time_axis == "recv_ts"


def test_analysis_config_rejects_invalid_numeric_ranges() -> None:
    """Config should validate required numeric constraints."""
    with pytest.raises(ValueError, match="counter_bits must be >= 1"):
        AnalysisConfig(counter_bits=0)

    with pytest.raises(ValueError, match="bucket_size_s must be > 0"):
        AnalysisConfig(bucket_size_s=0)

    with pytest.raises(ValueError, match="expected_period_s must be > 0"):
        AnalysisConfig(expected_period_s=-0.01)


def test_analysis_config_rejects_invalid_time_axis() -> None:
    """Only documented time axes should be accepted."""
    with pytest.raises(ValueError, match="default_time_axis must be one of"):
        AnalysisConfig(default_time_axis="message_time")


def test_analysis_config_is_immutable() -> None:
    """Config should be immutable once created."""
    cfg = AnalysisConfig()

    with pytest.raises(FrozenInstanceError):
        cfg.counter_bits = 32  # type: ignore[misc]


def test_normalized_record_minimal_construction() -> None:
    """Normalized records should accept required fields and optional topic."""
    row = NormalizedRawRecord(
        stream_id="stream-1",
        send_ts=100_000_000,
        recv_ts=100_010_000,
        counter=4,
        size_bytes=2048,
    )

    assert row.stream_id == "stream-1"
    assert row.topic is None
    assert row.send_ts == 100_000_000
    assert row.recv_ts == 100_010_000
    assert row.counter == 4
    assert row.size_bytes == 2048


def test_normalized_record_rejects_non_integer_microsecond_timestamps() -> None:
    """Normalized records should enforce integer microsecond timestamps."""
    with pytest.raises(TypeError, match="send_ts and recv_ts must be integer microseconds"):
        NormalizedRawRecord(
            stream_id="stream-1",
            send_ts=100.0,  # type: ignore[arg-type]
            recv_ts=100_010_000,
            counter=4,
            size_bytes=128,
        )

    with pytest.raises(TypeError, match="send_ts and recv_ts must be integer microseconds"):
        NormalizedRawRecord(
            stream_id="stream-1",
            send_ts=100_000_000,
            recv_ts="100010000",  # type: ignore[arg-type]
            counter=4,
            size_bytes=128,
        )


def test_normalized_record_rejects_bad_counter_and_size() -> None:
    """Normalized records should validate value ranges for size/counter."""
    with pytest.raises(ValueError, match="size_bytes must be >= 0"):
        NormalizedRawRecord(
            stream_id="stream-1",
            send_ts=100_000_000,
            recv_ts=100_010_000,
            counter=4,
            size_bytes=-1,
        )

    with pytest.raises(TypeError, match="counter must be an integer"):
        NormalizedRawRecord(
            stream_id="stream-1",
            send_ts=100_000_000,
            recv_ts=100_010_000,
            counter=4.2,  # type: ignore[arg-type]
            size_bytes=128,
        )
