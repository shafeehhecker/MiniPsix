"""
Mini-P6 — CPM Scheduler
========================
Application entry point.

Responsibilities
----------------
- Bootstrap the Qt application with sensible defaults.
- Apply a consistent font stack with cross-platform fallbacks.
- Set application metadata used by Qt's settings / OS integration.
- Provide a clean, informative crash handler so unhandled exceptions
  are shown to the user rather than silently terminating the process.
- Launch the main window and enter the Qt event loop.
"""

from __future__ import annotations

import os
import sys
import traceback

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so all relative imports resolve
# regardless of how the script is invoked (e.g. `python main.py` vs
# `python -m mini_p6` from a parent directory).
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# ---------------------------------------------------------------------------
# Qt imports — kept after sys.path fix so PySide6 can find any bundled libs
# ---------------------------------------------------------------------------
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from main_window import MainWindow

# ---------------------------------------------------------------------------
# Application metadata
# ---------------------------------------------------------------------------
APP_NAME        = "Mini-P6"
APP_VERSION     = "1.0.0"
ORGANIZATION    = "OpenPlan"
ORGANIZATION_URL = "https://openplan.example.com"  # update when live


# ---------------------------------------------------------------------------
# Font helpers
# ---------------------------------------------------------------------------

def _build_font() -> QFont:
    """
    Return the preferred UI font with cross-platform fallbacks.

    Priority:
        1. Segoe UI      (Windows)
        2. SF Pro Text   (macOS 10.11+)
        3. Ubuntu        (Ubuntu Linux)
        4. Roboto        (other Linux / Android)
        5. Sans-Serif    (Qt built-in generic fallback)
    """
    candidates = ["Segoe UI", "SF Pro Text", "Ubuntu", "Roboto", "Sans-Serif"]
    for family in candidates:
        font = QFont(family, 10)
        if font.exactMatch() or family == candidates[-1]:
            font.setPointSize(10)
            font.setStyleStrategy(QFont.PreferAntialias)
            return font
    return QFont()  # absolute fallback


# ---------------------------------------------------------------------------
# Unhandled-exception handler
# ---------------------------------------------------------------------------

def _excepthook(exc_type, exc_value, exc_tb) -> None:
    """
    Global exception handler.

    For unexpected runtime errors, display a user-friendly dialog with the
    traceback so the user can report the issue, then exit cleanly.
    Keyboard interrupts (Ctrl-C) still exit silently.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return

    tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(tb_text, file=sys.stderr)  # always echo to stderr / terminal

    # Show a dialog if a QApplication already exists
    if QApplication.instance():
        msg = QMessageBox()
        msg.setWindowTitle(f"{APP_NAME} — Unexpected Error")
        msg.setIcon(QMessageBox.Critical)
        msg.setText(
            "<b>An unexpected error occurred.</b><br>"
            "Please copy the details below and report this issue."
        )
        msg.setDetailedText(tb_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

    sys.exit(1)


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def _create_app() -> QApplication:
    """Initialise and configure the QApplication instance."""

    # High-DPI support — must be set *before* QApplication is constructed.
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)

    # Metadata (used by QSettings, OS task-bar, about dialogs, etc.)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(ORGANIZATION)
    app.setOrganizationDomain(ORGANIZATION_URL)

    # Font
    app.setFont(_build_font())

    # Optional: application icon (no-op if the file doesn't exist yet)
    icon_path = os.path.join(_PROJECT_ROOT, "resources", "icons", "app_icon.png")
    if os.path.isfile(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    return app


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Bootstrap Mini-P6 and start the Qt event loop."""

    # Install global exception handler before anything else can raise
    sys.excepthook = _excepthook

    app = _create_app()

    window = MainWindow()
    window.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}")
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
