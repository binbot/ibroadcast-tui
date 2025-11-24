# iBroadcast TUI

A terminal user interface (TUI) for the iBroadcast music service.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ibroadcast-tui.git
   cd ibroadcast-tui
   ```

2. Install dependencies with Poetry:
   ```bash
   poetry install
   ```

3. Configure your API credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your iBroadcast API credentials
   ```

## Usage

Run the application:
```bash
poetry run python -m ibroadcast_tui
```

## Development

- **Run tests**: `poetry run pytest`
- **Lint code**: `poetry run ruff check .`
- **Format code**: `poetry run ruff format .`
- **Type check**: `poetry run mypy src/`

## License

MIT
