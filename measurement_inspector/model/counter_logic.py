"""Counter delta and inferred loss computation for canonical base tables."""

from __future__ import annotations

import pandas as pd

from measurement_inspector.config.schema import AnalysisConfig


def apply_counter_derived_metrics(
    base_table: pd.DataFrame,
    config: AnalysisConfig | None = None,
) -> pd.DataFrame:
    """Compute stream-local counter deltas, inferred loss, and counter flags.

    The first row in each stream keeps null values for counter-derived fields because
    no previous observation exists.
    """
    resolved_config = config or AnalysisConfig()
    modulus = (
        resolved_config.counter_modulus
        if resolved_config.counter_modulus is not None
        else 2**resolved_config.counter_bits
    )

    result = base_table.copy()
    grouped = result.groupby("stream_id", sort=False, dropna=False)
    raw_delta = grouped["counter"].diff()

    delta = raw_delta.copy()
    if resolved_config.counter_wrap:
        prev_counter = grouped["counter"].shift(1)
        wrap_mask = (
            raw_delta.notna()
            & (raw_delta < 0)
            & ((-raw_delta) > (modulus / 2))
            & prev_counter.notna()
        )
        delta = delta.where(~wrap_mask, raw_delta + modulus)

    result["counter_delta"] = delta.astype("Int64")

    lost_msgs = pd.Series(0, index=result.index, dtype="Int64")
    positive_delta_mask = delta.notna() & (delta > 0)
    lost_msgs = lost_msgs.where(~positive_delta_mask, (delta - 1).clip(lower=0))
    result["lost_msgs"] = lost_msgs.astype("Int64")

    is_gap = (delta > 1).astype("boolean")
    is_counter_nonmonotonic = (delta <= 0).astype("boolean")

    first_row_mask = delta.isna()
    result["is_gap"] = is_gap.where(~first_row_mask, pd.NA).astype("boolean")
    result["is_counter_nonmonotonic"] = is_counter_nonmonotonic.where(
        ~first_row_mask, pd.NA
    ).astype("boolean")
    result.loc[first_row_mask, "lost_msgs"] = pd.NA

    return result
