# Graang Tests

This directory contains tests for the Graang project, which is a tool for converting Datadog dashboards to Grafana.

## Running Tests

You can run the tests in one of two ways:

1. Using the provided script:
   ```bash
   ./run_tests.py
   ```

2. Directly with pytest:
   ```bash
   # If using the virtual environment:
   ./venv/bin/pytest -v tests/
   
   # If pytest is installed globally:
   pytest -v tests/
   ```

## Test Structure

The tests are organized by module:

- `test_datadog_to_grafana.py`: Tests for the Datadog to Grafana conversion functionality

## Adding New Tests

When adding new tests, follow these guidelines:

1. Create a new test file with the name pattern `test_*.py`
2. Use the unittest framework for consistency
3. Add appropriate mocks to avoid external dependencies
4. Keep tests isolated and focused on specific functionality

## Test Coverage

To run tests with coverage reporting:

```bash
./venv/bin/pip install pytest-cov
./venv/bin/pytest --cov=. tests/
```