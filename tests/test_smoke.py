"""Smoke tests for test runner and package import."""


def test_pytest_smoke() -> None:
    """Ensure pytest discovers and executes tests."""
    assert True


def test_package_import_smoke() -> None:
    """Ensure the measurement_inspector package is importable."""
    import measurement_inspector

    assert measurement_inspector.__version__
