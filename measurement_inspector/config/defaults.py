"""Default configuration helpers."""

from __future__ import annotations

from measurement_inspector.config.schema import AnalysisConfig


def default_analysis_config() -> AnalysisConfig:
    """Return the baseline config used when no overrides are provided."""
    return AnalysisConfig()
