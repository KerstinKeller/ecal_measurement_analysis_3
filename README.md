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
