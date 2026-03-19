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
