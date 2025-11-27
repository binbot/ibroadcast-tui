# iBroadcast TUI

A terminal user interface (TUI) for the iBroadcast music service.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ibroadcast-tui.git
   cd ibroadcast-tui
   ```

2. Install system dependencies (Required for audio playback):

   - **macOS**:
     ```bash
     brew install mpv
     ```
   - **Fedora**:
     ```bash
     sudo dnf install mpv
     ```
   - **Arch Linux**:
     ```bash
     sudo pacman -S mpv
     ```
   - **Ubuntu/Debian**:
     ```bash
     sudo apt install mpv libmpv-dev
     ```

3. Install Python dependencies:
   
   **Option 1: pip (Recommended for most users)**
   ```bash
   pip install -r requirements.txt
   ```
   
   **Option 2: Poetry (For developers)**
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

**pip method:**
```bash
python -m ibroadcast_tui
```

**Poetry method:**
```bash
poetry run python -m ibroadcast_tui
```

## Development

### Setup Development Environment
```bash
# pip method:
pip install -r requirements-dev.txt

# Poetry method:
poetry install --with dev
```

### Development Commands
- **Run tests**: `poetry run pytest` or `pytest`
- **Lint code**: `poetry run ruff check .` or `ruff check .`
- **Format code**: `poetry run ruff format .` or `ruff format .`
- **Type check**: `poetry run mypy src/` or `mypy src/`

## License

MIT
