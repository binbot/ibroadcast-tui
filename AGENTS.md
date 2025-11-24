# iBroadcast TUI - Agent Guidelines

## Development Commands
- **Install dependencies**: `poetry install`
- **Run tests**: `poetry run pytest`
- **Run single test**: `poetry run pytest tests/test_file.py::test_function`
- **Lint code**: `poetry run ruff check .`
- **Format code**: `poetry run ruff format .`
- **Type check**: `poetry run mypy src/`
- **Run app**: `poetry run python -m ibroadcast_tui`

## Code Style Guidelines
- **Imports**: Use `isort` ordering, group stdlib, third-party, local imports
- **Formatting**: Use `ruff` with default settings (100 char line length)
- **Types**: Use strict type hints, return types required for all functions
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Error handling**: Use specific exceptions, never bare except clauses
- **Docstrings**: Google style for all public functions and classes
- **Testing**: Use pytest, aim for >80% coverage, mock external APIs

## Project Structure
- `src/ibroadcast_tui/` - Main package
- `tests/` - Test suite matching src structure
- Use Poetry for dependency management
- Python 3.14+ required