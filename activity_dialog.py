"""
Dialog for adding or editing an Activity.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QSpinBox, QDialogButtonBox, QLabel,
    QPushButton, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from engine.activity import Activity


class ActivityDialog(QDialog):
    """Modal dialog to create or edit an activity."""

    def __init__(self, parent=None, activity: Activity = None, existing_ids: list = None):
        super().__init__(parent)
        self.existing_ids = existing_ids or []
        self.edit_mode = activity is not None
        self._setup_ui(activity)

    def _setup_ui(self, activity: Activity = None):
        self.setWindowTitle("Edit Activity" if self.edit_mode else "Add Activity")
        self.setMinimumWidth(420)
        self.setModal(True)

        # Apply dark theme to dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #1e2530;
                color: #c8d0dc;
            }
            QLabel {
                color: #8a9bb0;
                font-size: 12px;
            }
            QLineEdit, QSpinBox {
                background-color: #252d3a;
                color: #e0e8f0;
                border: 1px solid #3a4558;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 1px solid #4a7fa8;
            }
            QLineEdit[readOnly="true"] {
                background-color: #1a2030;
                color: #5a6a7a;
            }
            QPushButton {
                background-color: #2a3545;
                color: #c0ccd8;
                border: 1px solid #3a4558;
                border-radius: 4px;
                padding: 7px 18px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #354255;
                color: #e0ecf8;
            }
            QPushButton[accent="true"] {
                background-color: #1e5c8a;
                color: #e0f0ff;
                border: 1px solid #2d7ab0;
                font-weight: bold;
            }
            QPushButton[accent="true"]:hover {
                background-color: #2570a0;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # Title label
        title_lbl = QLabel("Edit Activity" if self.edit_mode else "New Activity")
        title_lbl.setStyleSheet("color: #90b8d8; font-size: 16px; font-weight: bold;")
        root.addWidget(title_lbl)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #2a3545;")
        root.addWidget(line)

        # Form
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText("e.g. A, B, ACT-01 ...")
        if self.edit_mode and activity:
            self.id_edit.setText(activity.id)
            self.id_edit.setReadOnly(True)
        form.addRow("Activity ID:", self.id_edit)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Activity description")
        if activity:
            self.name_edit.setText(activity.name)
        form.addRow("Name:", self.name_edit)

        self.duration_spin = QSpinBox()
        self.duration_spin.setMinimum(0)
        self.duration_spin.setMaximum(9999)
        self.duration_spin.setSuffix("  days")
        if activity:
            self.duration_spin.setValue(activity.duration)
        form.addRow("Duration:", self.duration_spin)

        self.pred_edit = QLineEdit()
        self.pred_edit.setPlaceholderText("e.g. A,B (comma-separated IDs, leave blank if none)")
        if activity:
            self.pred_edit.setText(",".join(activity.predecessors))
        form.addRow("Predecessors:", self.pred_edit)

        root.addLayout(form)

        # Hint label
        hint = QLabel("Predecessors: comma-separated IDs of activities that must finish before this one starts (FS only).")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #4a5a6a; font-size: 11px; font-style: italic;")
        root.addWidget(hint)

        root.addSpacing(8)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        ok_btn = QPushButton("Save Activity")
        ok_btn.setProperty("accent", True)
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self._on_accept)
        btn_row.addWidget(ok_btn)

        root.addLayout(btn_row)

        # Error label (hidden by default)
        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet("color: #e05060; font-size: 12px;")
        self.error_lbl.hide()
        root.addWidget(self.error_lbl)

    def _on_accept(self):
        act_id = self.id_edit.text().strip()
        name = self.name_edit.text().strip()
        duration = self.duration_spin.value()
        preds_raw = self.pred_edit.text().strip()

        # Validate
        if not act_id:
            self._show_error("Activity ID cannot be empty.")
            return
        if not name:
            self._show_error("Name cannot be empty.")
            return
        if not self.edit_mode and act_id in self.existing_ids:
            self._show_error(f"ID '{act_id}' already exists.")
            return

        self.accept()

    def _show_error(self, msg: str):
        self.error_lbl.setText("⚠  " + msg)
        self.error_lbl.show()

    def get_activity(self) -> Activity:
        """Return the Activity built from dialog inputs."""
        act_id = self.id_edit.text().strip()
        name = self.name_edit.text().strip()
        duration = self.duration_spin.value()
        preds_raw = self.pred_edit.text().strip()
        preds = [p.strip() for p in preds_raw.split(",") if p.strip()]
        return Activity(id=act_id, name=name, duration=duration, predecessors=preds)
