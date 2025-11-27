import sys
try:
    import mpv
    print(f"python-mpv version: {mpv.__version__}")
    print("Attempting to initialize MPV...")
    player = mpv.MPV(log_handler=print)
    print("MPV initialized successfully")
    player.terminate()
except Exception as e:
    print(f"Failed: {e}")
    import traceback
    traceback.print_exc()
