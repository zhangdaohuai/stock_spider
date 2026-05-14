# Testing with pytest

Configuration and best practices for pytest with coverage enforcement.

## Setup

```bash
uv add --group test pytest pytest-cov hypothesis
```

## pyproject.toml Configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = [
    "-ra",
    "--strict-markers",
    "--strict-config",
    "--cov=myproject",
    "--cov-report=term-missing",
    "--cov-fail-under=80",
]
markers = [
    "slow: marks tests as slow",
    "integration: marks integration tests",
]
filterwarnings = [
    "error",
    "ignore::DeprecationWarning:third_party.*",
]

[tool.coverage.run]
branch = true
source = ["src/myproject"]
omit = [
    "*/__main__.py",
    "*/conftest.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
    "raise NotImplementedError",
    "@abstractmethod",
]
fail_under = 80
show_missing = true
```

## Project Structure

```
myproject/
├── src/
│   └── myproject/
│       ├── __init__.py
│       └── core.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_core.py
│   └── integration/
│       └── test_api.py
└── pyproject.toml
```

## Running Tests

```bash
uv run pytest
uv run pytest -v
uv run pytest tests/test_core.py
uv run pytest tests/test_core.py::test_function_name
uv run pytest -k "test_parse"
uv run pytest -m "not slow"
uv run pytest -x
uv run pytest --lf
```

## Coverage Commands

```bash
uv run pytest --cov=myproject
uv run pytest --cov=myproject --cov-report=html
uv run coverage report
uv run coverage html
```

## Makefile Target

```makefile
.PHONY: test test-cov test-fast

test:
	uv run pytest

test-cov:
	uv run pytest --cov-report=html
	open htmlcov/index.html

test-fast:
	uv run pytest -x -q --no-cov
```

## CI Configuration

```yaml
- name: Run tests
  run: |
    uv sync --group test
    uv run pytest --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v4
  with:
    files: ./coverage.xml
```
