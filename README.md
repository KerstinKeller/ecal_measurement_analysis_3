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
