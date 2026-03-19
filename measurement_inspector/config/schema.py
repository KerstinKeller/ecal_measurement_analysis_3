"""Typed configuration schema for the measurement analysis pipeline."""

from __future__ import annotations

from dataclasses import dataclass

_VALID_TIME_AXES = {"recv_ts", "send_ts"}


@dataclass(frozen=True, slots=True)
class AnalysisConfig:
    """Configuration options used across analysis layers."""

    counter_bits: int = 16
    counter_wrap: bool = True
    counter_modulus: int | None = None
    duplicate_policy: str = "flag"
    reorder_policy: str = "flag"
    expected_period_s: float | None = None
    expected_freq_hz: float | None = None
    latency_warn_s: float | None = None
    period_error_warn_s: float | None = None
    bucket_size_s: float = 1.0
    max_raw_points_before_rasterize: int = 200_000
    default_time_axis: str = "recv_ts"

    def __post_init__(self) -> None:
        if self.counter_bits < 1:
            raise ValueError("counter_bits must be >= 1")

        if self.counter_modulus is not None and self.counter_modulus < 1:
            raise ValueError("counter_modulus must be >= 1 when provided")

        if self.expected_period_s is not None and self.expected_period_s <= 0:
            raise ValueError("expected_period_s must be > 0 when provided")

        if self.expected_freq_hz is not None and self.expected_freq_hz <= 0:
            raise ValueError("expected_freq_hz must be > 0 when provided")

        if self.latency_warn_s is not None and self.latency_warn_s <= 0:
            raise ValueError("latency_warn_s must be > 0 when provided")

        if self.period_error_warn_s is not None and self.period_error_warn_s <= 0:
            raise ValueError("period_error_warn_s must be > 0 when provided")

        if self.bucket_size_s <= 0:
            raise ValueError("bucket_size_s must be > 0")

        if self.max_raw_points_before_rasterize < 1:
            raise ValueError("max_raw_points_before_rasterize must be >= 1")

        if self.default_time_axis not in _VALID_TIME_AXES:
            allowed = ", ".join(sorted(_VALID_TIME_AXES))
            raise ValueError(f"default_time_axis must be one of: {allowed}")
