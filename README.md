# measurement-inspector

Local Python application for inspecting one eCAL measurement at a time.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Run quality checks

```bash
pytest
ruff check .
ruff format --check .
```

## Package layout

Core package namespace: `measurement_inspector`.

## Core contracts (Step 1.1)

### Analysis configuration

`measurement_inspector.config.schema.AnalysisConfig` defines pipeline-level defaults and validation for:

- counter behavior (`counter_bits`, `counter_wrap`, optional `counter_modulus`)
- expected timing references (`expected_period_s`, `expected_freq_hz`)
- warning thresholds (`latency_warn_s`, `period_error_warn_s`)
- aggregation/rendering controls (`bucket_size_s`, `max_raw_points_before_rasterize`)
- default time axis (`default_time_axis`, either `recv_ts` or `send_ts`)

Use `measurement_inspector.config.defaults.default_analysis_config()` to construct baseline defaults.

### Normalized raw message record

`measurement_inspector.io.record_models.NormalizedRawRecord` is the canonical normalized adapter record with required fields:

- `stream_id`
- `send_ts` (integer microseconds)
- `recv_ts` (integer microseconds)
- `counter`
- `size_bytes`

And optional field:

- `topic`

The model validates type/range requirements so downstream modeling code receives a stable contract, including integer-microsecond timestamps as produced by the measurement adapter.

### Adapter protocol and synthetic fixtures (Step 1.2)

`measurement_inspector.io.ecal_reader.MeasurementAdapter` defines the analysis-facing adapter contract:

- `list_streams(measurement_path)` returns stream metadata as a dataframe
- `iter_messages(measurement_path, stream_ids=None, topics=None)` yields `NormalizedRawRecord` rows

For test-driven downstream work, synthetic builders and a minimal fake adapter are provided in
`tests/synthetic_fixtures.py`:

- `build_synthetic_record(...)`
- `build_synthetic_stream(...)`
- `FakeMeasurementAdapter`

These helpers provide deterministic stream/message fixtures without requiring real eCAL integration.

### Canonical base table (Step 2.1)

`measurement_inspector.model.base_table.build_base_table(records)` converts normalized records into the
canonical **observed-message** dataframe:

- one row per observed message (no synthetic missing-message rows)
- one combined table across streams, keyed by `stream_id`
- deterministic default order by `stream_id`, then receiver-time analysis order
- raw normalized fields are preserved exactly (`stream_id`, `topic`, `send_ts`, `recv_ts`, `counter`, `size_bytes`)
- derived/anomaly columns are provisioned as nullable placeholders for later modeling steps


### Timing-derived metrics (Step 2.2)

`measurement_inspector.model.derived_metrics.apply_timing_derived_metrics(base_table)` computes
stream-local timing diagnostics on the canonical table:

- `latency_s = (recv_ts - send_ts) / 1_000_000`
- `send_dt_s`: per-stream delta between consecutive `send_ts` values
- `recv_dt_s`: per-stream delta between consecutive `recv_ts` values
- `is_send_time_nonmonotonic`: `True` when `send_dt_s < 0`, otherwise `False`, and null on first row per stream
- `is_recv_time_nonmonotonic`: `True` when `recv_dt_s < 0`, otherwise `False`, and null on first row per stream

All first rows per stream keep null deltas/flags because no previous observation exists.

### Counter-derived metrics and inferred loss (Step 3.1)

`measurement_inspector.model.counter_logic.apply_counter_derived_metrics(base_table, config=None)`
computes stream-local counter diagnostics on the canonical base table:

- `counter_delta`: effective counter increment from previous observed row in the same stream
- `lost_msgs`: inferred missing messages (`max(counter_delta - 1, 0)`) for forward motion
- `is_gap`: `True` when `counter_delta > 1`
- `is_counter_nonmonotonic`: `True` for duplicate (`delta == 0`) or backward (`delta < 0`) motion

Wrap-aware behavior is controlled by `AnalysisConfig`:

- modulus is `counter_modulus` when provided, otherwise `2 ** counter_bits`
- when `counter_wrap=True`, negative deltas are normalized as wrap only for large
  backward jumps (`abs(raw_delta) > modulus / 2`), preserving small backward jumps
  as non-monotonic reorder/backward events
- when `counter_wrap=False`, raw signed deltas are used directly

The first row per stream keeps null values for all counter-derived fields.

### Loss-event table (Step 3.2)

`measurement_inspector.model.summaries.build_loss_event_table(base_table)` extracts a
separate inferred loss-event table from the canonical observed-message base table:

- emits one row per inferred counter gap (`is_gap == True`)
- carries previous/current sender and receiver timestamps and counters
- includes derived gap values (`recv_gap_s`, `send_gap_s`)
- includes `latency_before_s` and `latency_after_s` for before/after event inspection

This keeps **observed-message semantics** in the base table while representing inferred
missing-message behavior in a dedicated event table.
