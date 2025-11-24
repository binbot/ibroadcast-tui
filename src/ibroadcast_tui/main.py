"""Main entry point for the iBroadcast TUI application."""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static

class iBroadcastApp(App):
    """Main iBroadcast TUI application."""
    
    def __init__(self) -> None:
        """Initialize the app with correct title."""
        super().__init__()
        self.title = "iBroadcast TUI"
    
    CSS = """
    Screen {
        layout: vertical;
    }
    
    #welcome {
        text-align: center;
        padding: 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Create the main layout."""
        yield Header()
        yield Static("Welcome to iBroadcast TUI", id="welcome")
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when the app starts."""
        pass

if __name__ == "__main__":
    app = iBroadcastApp()
    app.run()
