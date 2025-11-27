"""Main entry point for the iBroadcast TUI application."""

from .ui.app import iBroadcastTUI

def main():
    """Run the application."""
    app = iBroadcastTUI()
    app.run()

if __name__ == "__main__":
    main()
