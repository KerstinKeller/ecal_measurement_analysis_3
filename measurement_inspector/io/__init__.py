"""I/O contracts and adapters."""

from measurement_inspector.io.ecal_reader import MeasurementAdapter
from measurement_inspector.io.record_models import NormalizedRawRecord

__all__ = ["MeasurementAdapter", "NormalizedRawRecord"]
