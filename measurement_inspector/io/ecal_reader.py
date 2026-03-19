"""Adapter contracts for reading and normalizing eCAL measurement data."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, runtime_checkable

import pandas as pd

from measurement_inspector.io.record_models import NormalizedRawRecord


@runtime_checkable
class MeasurementAdapter(Protocol):
    """Narrow adapter contract consumed by downstream analysis layers."""

    def list_streams(self, measurement_path: str) -> pd.DataFrame:
        """Return one row per available stream for the given measurement path."""

    def iter_messages(
        self,
        measurement_path: str,
        stream_ids: list[str] | None = None,
        topics: list[str] | None = None,
    ) -> Iterable[NormalizedRawRecord]:
        """Yield normalized message records from the measurement source."""
