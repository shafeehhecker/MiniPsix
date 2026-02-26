"""
Dialog for adding or editing a CPM Activity.

Provides a styled modal QDialog that:
  - Creates a new Activity (add mode) or pre-fills fields for an existing one (edit mode).
  - Validates all inputs before accepting, showing inline error messages.
  - Optionally validates that predecessor IDs reference activities that actually exist.
  - Exposes ``get_activity()`` to retrieve the fully constructed Activity instance.
"""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QFont, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QFormLayout,
    QWidget,
)

from activity import Activity


# ---------------------------------------------------------------------------
# Style constants — centralised so a future theme switch touches one place
# ---------------------------------------------------------------------------

_DIALOG_QSS = """
QDialog {
    background-color: #1e2530;
    color: #c8d0dc;
}

/* ── Labels ── */
QLabel {
    color: #8a9bb0;
    font-size: 12px;
}
QLabel#title_label {
    color: #90b8d8;
    font-size: 16px;
    font-weight: bold;
}
QLabel#section_label {
    color: #6a8aa8;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
    text-transform: uppercase;
}
QLabel#hint_label {
    color: #4a5a6a;
    font-size: 11px;
    font-style: italic;
}
QLabel#error_label {
    color: #e05060;
    font-size: 12px;
    background-color: #2a1a1e;
    border: 1px solid #6a2530;
    border-radius: 4px;
    padding: 5px 8px;
}
QLabel#success_label {
    color: #50c878;
    font-size: 12px;
}

/* ── Inputs ── */
QLineEdit, QSpinBox {
    background-color: #252d3a;
    color: #e0e8f0;
    border: 1px solid #3a4558;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 13px;
    min-height: 28px;
}
QLineEdit:focus, QSpinBox:focus {
    border: 1px solid #4a7fa8;
    background-color: #2a3545;
}
QLineEdit:hover, QSpinBox:hover {
    border: 1px solid #506070;
}
QLineEdit[readOnly="true"] {
    background-color: #1a2030;
    color: #5a7088;
    border: 1px solid #2a3040;
}
QLineEdit[valid="false"] {
    border: 1px solid #8a3040;
    background-color: #2a1e25;
}
QLineEdit[valid="true"] {
    border: 1px solid #2a6840;
}

/* ── Buttons ── */
QPushButton {
    background-color: #2a3545;
    color: #c0ccd8;
    border: 1px solid #3a4558;
    border-radius: 4px;
    padding: 7px 18px;
    font-size: 12px;
    min-width: 80px;
}
QPushButton:hover {
    background-color: #354255;
    color: #e0ecf8;
}
QPushButton:pressed {
    background-color: #1e2e40;
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
QPushButton[accent="true"]:pressed {
    background-color: #184a70;
}
QPushButton[accent="true"]:disabled {
    background-color: #1a3550;
    color: #4a6a80;
    border: 1px solid #1e3a50;
}

/* ── Divider ── */
QFrame[frameShape="4"],   /* HLine */
QFrame[frameShape="5"] {  /* VLine */
    color: #2a3545;
    background-color: #2a3545;
    max-height: 1px;
}
"""


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------

class ActivityDialog(QDialog):
    """
    Modal dialog to create or edit a CPM Activity.

    Parameters
    ----------
    parent : QWidget, optional
        Parent widget (for modality and positioning).
    activity : Activity, optional
        If provided, the dialog opens in *edit mode* with all fields pre-filled.
        The Activity ID field is locked in this mode.
    existing_ids : list[str], optional
        IDs already present in the project.  Used to prevent duplicate IDs when
        adding a new activity.
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        activity: Optional[Activity] = None,
        existing_ids: Optional[List[str]] = None,
    ) -> None:
        super().__init__(parent)

        self._existing_ids: List[str] = [str(i) for i in (existing_ids or [])]
        self._edit_mode: bool = activity is not None

        self._build_ui(activity)
        self._connect_signals()

    # ------------------------------------------------------------------ #
    # UI construction                                                      #
    # ------------------------------------------------------------------ #

    def _build_ui(self, activity: Optional[Activity]) -> None:
        """Construct and arrange all widgets."""

        self.setWindowTitle("Edit Activity" if self._edit_mode else "Add Activity")
        self.setMinimumWidth(460)
        self.setModal(True)
        self.setStyleSheet(_DIALOG_QSS)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        # ── Title ──────────────────────────────────────────────────────
        title_text = "Edit Activity" if self._edit_mode else "New Activity"
        self._title_lbl = QLabel(title_text)
        self._title_lbl.setObjectName("title_label")
        root.addWidget(self._title_lbl)

        root.addWidget(self._make_divider())

        # ── Form ───────────────────────────────────────────────────────
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        # Activity ID
        self._id_edit = QLineEdit()
        self._id_edit.setPlaceholderText("e.g. A, B, ACT-01 …")
        self._id_edit.setMaxLength(32)
        if self._edit_mode and activity:
            self._id_edit.setText(activity.id)
            self._id_edit.setReadOnly(True)
            self._id_edit.setToolTip("Activity ID cannot be changed in edit mode.")
        else:
            self._id_edit.setToolTip("Unique identifier for this activity.")
        form.addRow("Activity ID *", self._id_edit)

        # Name
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Short description of work to be done")
        self._name_edit.setMaxLength(120)
        if activity:
            self._name_edit.setText(activity.name)
        self._name_edit.setToolTip("Human-readable activity name.")
        form.addRow("Name *", self._name_edit)

        # Duration
        self._duration_spin = QSpinBox()
        self._duration_spin.setMinimum(0)
        self._duration_spin.setMaximum(9_999)
        self._duration_spin.setSuffix("  days")
        self._duration_spin.setToolTip(
            "Duration in working days.  Use 0 for milestones."
        )
        if activity:
            self._duration_spin.setValue(activity.duration)
        form.addRow("Duration *", self._duration_spin)

        # Predecessors
        self._pred_edit = QLineEdit()
        self._pred_edit.setPlaceholderText("e.g. A, B  (blank = no predecessors)")
        self._pred_edit.setToolTip(
            "Comma-separated IDs of activities that must finish before this one starts.\n"
            "Only Finish-to-Start (FS) relationships are supported."
        )
        if activity:
            self._pred_edit.setText(",".join(activity.predecessors))
        form.addRow("Predecessors", self._pred_edit)

        # Resource (new optional field)
        self._resource_edit = QLineEdit()
        self._resource_edit.setPlaceholderText("e.g. Civil Team, John D.")
        self._resource_edit.setMaxLength(80)
        self._resource_edit.setToolTip("Responsible resource or team (optional, informational).")
        if activity and activity.resource:
            self._resource_edit.setText(activity.resource)
        form.addRow("Resource", self._resource_edit)

        # Description / Notes (new optional field)
        self._desc_edit = QLineEdit()
        self._desc_edit.setPlaceholderText("Additional notes or scope details (optional)")
        self._desc_edit.setMaxLength(255)
        self._desc_edit.setToolTip("Extended description or scope notes.")
        if activity and activity.description:
            self._desc_edit.setText(activity.description)
        form.addRow("Description", self._desc_edit)

        root.addLayout(form)

        # ── Hint ───────────────────────────────────────────────────────
        hint = QLabel(
            "* Required fields.  Predecessors must reference existing Activity IDs "
            "and cannot include this activity's own ID."
        )
        hint.setObjectName("hint_label")
        hint.setWordWrap(True)
        root.addWidget(hint)

        root.addSpacing(4)
        root.addWidget(self._make_divider())

        # ── Error / success feedback ───────────────────────────────────
        self._error_lbl = QLabel("")
        self._error_lbl.setObjectName("error_label")
        self._error_lbl.setWordWrap(True)
        self._error_lbl.hide()
        root.addWidget(self._error_lbl)

        # ── Buttons ────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setToolTip("Discard changes and close.")
        btn_row.addWidget(self._cancel_btn)

        self._ok_btn = QPushButton("Save Activity")
        self._ok_btn.setProperty("accent", True)
        self._ok_btn.setDefault(True)
        self._ok_btn.setToolTip("Validate and save this activity.")
        btn_row.addWidget(self._ok_btn)

        root.addLayout(btn_row)

    # ------------------------------------------------------------------ #
    # Signal wiring                                                        #
    # ------------------------------------------------------------------ #

    def _connect_signals(self) -> None:
        """Wire widget signals to slots."""
        self._cancel_btn.clicked.connect(self.reject)
        self._ok_btn.clicked.connect(self._on_accept)

        # Live validation feedback: clear error highlight when user edits
        self._id_edit.textChanged.connect(self._clear_error)
        self._name_edit.textChanged.connect(self._clear_error)
        self._pred_edit.textChanged.connect(self._clear_error)

    # ------------------------------------------------------------------ #
    # Validation                                                           #
    # ------------------------------------------------------------------ #

    def _validate(self) -> Optional[str]:
        """
        Validate all form fields.

        Returns
        -------
        str or None
            An error message string if validation fails, or ``None`` on success.
        """
        act_id = self._id_edit.text().strip()
        name = self._name_edit.text().strip()
        preds_raw = self._pred_edit.text().strip()

        # --- Required fields ---
        if not act_id:
            return "Activity ID cannot be empty."

        if not name:
            return "Activity name cannot be empty."

        # --- Duplicate ID check (add mode only) ---
        if not self._edit_mode and act_id in self._existing_ids:
            return f"Activity ID '{act_id}' already exists in this project."

        # --- Self-loop guard ---
        pred_list = [p.strip() for p in preds_raw.split(",") if p.strip()]
        if act_id in pred_list:
            return f"An activity cannot be its own predecessor ('{act_id}')."

        # --- Predecessor ID existence check (when existing_ids provided) ---
        if self._existing_ids:
            # In edit mode the current activity's id is already in existing_ids;
            # in add mode it is not yet — we don't add it here to keep this method pure.
            known_ids = set(self._existing_ids)
            unknown = [p for p in pred_list if p not in known_ids]
            if unknown:
                return (
                    f"Unknown predecessor ID(s): {', '.join(unknown)}.\n"
                    "Please check the IDs or add those activities first."
                )

        return None  # all good

    # ------------------------------------------------------------------ #
    # Slots                                                                #
    # ------------------------------------------------------------------ #

    def _on_accept(self) -> None:
        """Validate inputs; accept the dialog if valid, otherwise show error."""
        error = self._validate()
        if error:
            self._show_error(error)
        else:
            self._clear_error()
            self.accept()

    def _show_error(self, msg: str) -> None:
        """Display an inline error banner below the form."""
        self._error_lbl.setText("⚠  " + msg)
        self._error_lbl.show()

    def _clear_error(self) -> None:
        """Hide the error banner (called on user edit)."""
        if self._error_lbl.isVisible():
            self._error_lbl.hide()

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def get_activity(self) -> Activity:
        """
        Build and return the Activity from the current dialog inputs.

        Call this *after* ``exec()`` returns ``QDialog.Accepted``.

        Returns
        -------
        Activity
            Fully constructed Activity instance (CPM fields default to 0).
        """
        act_id = self._id_edit.text().strip()
        name = self._name_edit.text().strip()
        duration = self._duration_spin.value()
        preds = [p.strip() for p in self._pred_edit.text().split(",") if p.strip()]
        resource = self._resource_edit.text().strip() or None
        description = self._desc_edit.text().strip() or None

        return Activity(
            id=act_id,
            name=name,
            duration=duration,
            predecessors=preds,
            resource=resource,
            description=description,
        )

    # ------------------------------------------------------------------ #
    # Static / private helpers                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _make_divider() -> QFrame:
        """Return a styled horizontal rule widget."""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Plain)
        return line
