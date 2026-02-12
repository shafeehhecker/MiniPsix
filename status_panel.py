"""
Status and project summary panel shown at the bottom of the window.
"""
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from typing import Dict, List

from engine.activity import Activity


class StatusPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #131b24;
                border-top: 1px solid #2a3545;
            }
            QLabel {
                color: #3a5a78;
                font-size: 11px;
            }
            QLabel[highlight="true"] {
                color: #6a9ab8;
                font-weight: bold;
            }
            QLabel[critical="true"] {
                color: #c03040;
                font-weight: bold;
            }
        """)
        self.setFixedHeight(32)

        row = QHBoxLayout(self)
        row.setContentsMargins(14, 4, 14, 4)
        row.setSpacing(28)

        self.lbl_status = QLabel("Ready — load or add activities to begin.")
        row.addWidget(self.lbl_status)
        row.addStretch()

        # Stat pills
        self.lbl_total     = self._make_stat("Activities: —")
        self.lbl_duration  = self._make_stat("Project Duration: —")
        self.lbl_critical  = self._make_stat("Critical Path: —", critical=True)

        row.addWidget(self.lbl_total)
        row.addWidget(self.lbl_duration)
        row.addWidget(self.lbl_critical)

    def _make_stat(self, text: str, critical: bool = False) -> QLabel:
        lbl = QLabel(text)
        if critical:
            lbl.setProperty("critical", True)
        else:
            lbl.setProperty("highlight", True)
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
        color = "#e04050" if error else "#3a5a78"
        self.lbl_status.setStyleSheet(f"color: {color}; font-size: 11px;")
        self.lbl_status.setText(msg)
