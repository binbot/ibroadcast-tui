"""Main entry point for running the package."""

from .ui.app import iBroadcastTUI

if __name__ == "__main__":
    app = iBroadcastTUI()
    app.run()
