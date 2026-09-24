"""
Academic AI Interaction Protocol Logger & Exporter
Main Entry Point.

Run directly via:
    python app.py
Or click run.bat on Windows.
"""

import sys
import os

# Ensure project directory is in python search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def enable_windows_high_dpi():
    """Enables crisp high-DPI scaling on Windows displays."""
    if sys.platform == "win32":
        try:
            import ctypes
            # Try Windows 10/11 Per-Monitor V2 DPI awareness
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                # Fallback to system DPI awareness
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def main():
    enable_windows_high_dpi()
    from gui.main_window import MainWindow

    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
