"""
Status and project summary panel shown at the bottom of the window.
Advanced professional light theme with subtle shadows and refined styling.
"""

from typing import Dict, List

from activity import Activity
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPalette
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel


class StatusPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        # Light, elevated panel with subtle top shadow and clean typography
        self.setStyleSheet("""
            QFrame {
                background-color: #fafafa;
                border-top: 1px solid #d0d0d0;
                border-bottom: none;
                border-left: none;
                border-right: none;
            }
            QLabel {
                color: #404040;
                font-size: 11px;
                font-weight: 400;
                padding: 2px 0;
            }
            QLabel[highlight="true"] {
                color: #1e5c8a;
                font-weight: 600;
            }
            QLabel[critical="true"] {
                color: #b03040;
                font-weight: 600;
            }
            QLabel#status_label {
                font-size: 12px;
                font-weight: 500;
                color: #202020;
                background-color: #f0f0f0;
                padding: 4px 12px;
                border-radius: 12px;
            }
        """)

        self.setFixedHeight(40)  # Slightly taller for better presence
        # Add a subtle drop shadow for elevation
        from PySide6.QtWidgets import QGraphicsDropShadowEffect

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(Qt.gray)
        shadow.setOffset(0, -2)
        self.setGraphicsEffect(shadow)

        row = QHBoxLayout(self)
        row.setContentsMargins(16, 6, 16, 6)
        row.setSpacing(24)

        # Status message with pill background
        self.lbl_status = QLabel("Ready — load or add activities to begin.")
        self.lbl_status.setObjectName("status_label")
        row.addWidget(self.lbl_status)
        row.addStretch()

        # Stat pills (no extra background, just text with highlights)
        self.lbl_total = self._make_stat("Activities: —")
        self.lbl_duration = self._make_stat("Project Duration: —")
        self.lbl_critical = self._make_stat("Critical Path: —", critical=True)

        row.addWidget(self.lbl_total)
        row.addWidget(self.lbl_duration)
        row.addWidget(self.lbl_critical)

    def _make_stat(self, text: str, critical: bool = False) -> QLabel:
        lbl = QLabel(text)
        if critical:
            lbl.setProperty("critical", True)
        else:
            lbl.setProperty("highlight", True)
        # Apply font weight via style already set; re-polish to ensure property takes effect
        lbl.style().unpolish(lbl)
        lbl.style().polish(lbl)
        return lbl

    def update_stats(self, activities: Dict[str, Activity], critical_ids: List[str]):
        n = len(activities)
        if n == 0:
            self.lbl_total.setText("Activities: 0")
            self.lbl_duration.setText("Project Duration: —")
            self.lbl_critical.setText("Critical Path: —")
            self.lbl_status.setText("No activities yet.")
            return

        dur = max((a.EF for a in activities.values()), default=0)
        cp_str = " → ".join(critical_ids) if critical_ids else "none"

        self.lbl_total.setText(f"Activities: {n}")
        self.lbl_duration.setText(f"Project Duration: {dur} days")
        self.lbl_critical.setText(f"Critical: {cp_str}")
        self.lbl_status.setText("CPM schedule computed successfully.")

    def set_message(self, msg: str, error: bool = False):
        if error:
            self.lbl_status.setStyleSheet("""
                QLabel#status_label {
                    color: #b03040;
                    background-color: #ffe0e0;
                    font-weight: 600;
                }
            """)
        else:
            self.lbl_status.setStyleSheet("""
                QLabel#status_label {
                    color: #202020;
                    background-color: #f0f0f0;
                }
            """)
        self.lbl_status.setText(msg)
