"""Main entry point for running the package."""

import sys
import os

# Add the src directory to Python path so imports work
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Check for simple mode
if len(sys.argv) > 1 and sys.argv[1] == "--simple":
    print("🎵 iBroadcast TUI - Simple Mode")
    print("=" * 50)

    try:
        from .api.client import iBroadcastClient
        from .config import settings

        print("🔗 Connecting to iBroadcast...")
        client = iBroadcastClient()

        # Try to authenticate
        auth_result = client.authenticate()
        if auth_result["status"] == "success":
            print("✅ Authentication successful!")

            # Load library
            print("📚 Loading music library...")
            library_result = client.get_library()

            if library_result["status"] == "success":
                data = library_result.get("data", {})
                albums_count = len(data.get("albums", {}))
                artists_count = len(data.get("artists", {}))
                tracks_count = len(data.get("tracks", {}))
                playlists_count = len(data.get("playlists", {}))

                print("✅ Library loaded successfully!")
                print(f"   📀 Albums: {albums_count}")
                print(f"   🎤 Artists: {artists_count}")
                print(f"   🎵 Tracks: {tracks_count}")
                print(f"   📋 Playlists: {playlists_count}")

                print("\n🎶 Your iBroadcast TUI is working!")
                print("The TUI interface may have display issues in your terminal.")
                print("Try a different terminal or check ANSI color support.")

            else:
                print(f"❌ Failed to load library: {library_result.get('message', 'Unknown error')}")

        else:
            print(f"❌ Authentication failed: {auth_result.get('message', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    sys.exit(0)

# Test mode
if len(sys.argv) > 1 and sys.argv[1] == "--test":
    print("🧪 Testing Textual...")
    try:
        from textual.app import App
        from textual.widgets import Static

        class TestApp(App):
            def compose(self):
                yield Static("🎵 TEXTUAL TEST - If you can see this, Textual is working!")

        app = TestApp()
        print("✅ Textual app created")
        print("🎬 Running test app...")
        app.run()
        print("✅ Test completed")
    except Exception as e:
        print(f"❌ Textual test failed: {e}")
        import traceback
        traceback.print_exc()
    sys.exit(0)

# Normal TUI mode
print("🎵 iBroadcast TUI Starting...")
print("💡 Tip: Run with --simple for basic text output")
print("🧪 Tip: Run with --test to test Textual")

try:
    from .ui.app import iBroadcastTUI
    print("✅ Imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("💡 Try: poetry run python -m ibroadcast_tui --simple")
    exit(1)

if __name__ == "__main__":
    print("🚀 Launching iBroadcast TUI...")
    try:
        app = iBroadcastTUI()
        print("✅ App created successfully")
        print("🎶 Starting TUI interface...")
        print("💡 If you see an empty box, try:")
        print("   poetry run python -m ibroadcast_tui --simple")
        print("   poetry run python -m ibroadcast_tui --test")
        app.run()
    except Exception as e:
        print(f"❌ App failed to start: {e}")
        print("💡 Try the simple mode: poetry run python -m ibroadcast_tui --simple")
        import traceback
        traceback.print_exc()
