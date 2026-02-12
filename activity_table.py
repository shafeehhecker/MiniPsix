"""
Activity Table widget — the core grid showing all CPM fields.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QHeaderView,
    QAbstractItemView, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QBrush

from engine.activity import Activity
from typing import Dict, Optional


# Column definitions: (header label, attribute name, width)
COLUMNS = [
    ("ID",          "id",          70),
    ("Activity Name","name",       200),
    ("Dur",         "duration",    55),
    ("Predecessors","predecessors",110),
    ("ES",          "ES",          55),
    ("EF",          "EF",          55),
    ("LS",          "LS",          55),
    ("LF",          "LF",          55),
    ("Float",       "total_float", 60),
    ("Critical",    "is_critical", 70),
]

COL_HEADERS  = [c[0] for c in COLUMNS]
COL_ATTRS    = [c[1] for c in COLUMNS]
COL_WIDTHS   = [c[2] for c in COLUMNS]

# Theme colours
CLR_BG          = QColor("#1e2530")
CLR_ROW_EVEN    = QColor("#212a36")
CLR_ROW_ODD     = QColor("#1a2230")
CLR_CRITICAL    = QColor("#3d1e22")
CLR_CRITICAL_FG = QColor("#ff6b7a")
CLR_HEADER_BG   = QColor("#151c26")
CLR_HEADER_FG   = QColor("#6a8fae")
CLR_FLOAT_ZERO  = QColor("#e05060")
CLR_TEXT        = QColor("#c8d8e8")
CLR_DIM         = QColor("#4a5a6a")
CLR_SELECT_BG   = QColor("#1e4a6a")


class ActivityTable(QWidget):
    """
    Left-side activity table.  Emits signals when the user interacts.
    """
    activity_selected = Signal(str)   # emits activity ID
    add_requested = Signal()
    edit_requested = Signal(str)      # emits activity ID
    delete_requested = Signal(str)    # emits activity ID

    def __init__(self, parent=None):
        super().__init__(parent)
        self._activities: Dict[str, Activity] = {}
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI Setup
    # ------------------------------------------------------------------

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QWidget {{ background-color: {CLR_BG.name()}; }}
            QTableWidget {{
                background-color: {CLR_BG.name()};
                color: {CLR_TEXT.name()};
                gridline-color: #2a3545;
                border: none;
                font-size: 12px;
                selection-background-color: {CLR_SELECT_BG.name()};
            }}
            QHeaderView::section {{
                background-color: {CLR_HEADER_BG.name()};
                color: {CLR_HEADER_FG.name()};
                padding: 5px 8px;
                border: none;
                border-right: 1px solid #2a3545;
                border-bottom: 2px solid #2a3545;
                font-size: 11px;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            QScrollBar:vertical {{
                background: #1a2230;
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: #3a4a5a;
                border-radius: 5px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = self._build_toolbar()
        layout.addWidget(toolbar)

        # Table
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COL_HEADERS)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(True)
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.setFocusPolicy(Qt.NoFocus)

        for i, w in enumerate(COL_WIDTHS):
            self.table.setColumnWidth(i, w)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)

    def _build_toolbar(self) -> QWidget:
        bar = QFrame()
        bar.setStyleSheet("""
            QFrame {
                background-color: #161e2a;
                border-bottom: 1px solid #2a3545;
            }
            QPushButton {
                background-color: transparent;
                color: #6a8fae;
                border: 1px solid #2a3545;
                border-radius: 4px;
                padding: 5px 14px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #252f3d;
                color: #90b8d8;
            }
            QPushButton#addBtn {
                background-color: #1e4a6a;
                color: #90d0f8;
                border: 1px solid #2a6a98;
            }
            QPushButton#addBtn:hover {
                background-color: #255878;
            }
            QPushButton#deleteBtn:hover {
                background-color: #3d1e22;
                color: #e05060;
                border-color: #6a2030;
            }
        """)
        row = QHBoxLayout(bar)
        row.setContentsMargins(10, 7, 10, 7)
        row.setSpacing(8)

        lbl = QLabel("ACTIVITIES")
        lbl.setStyleSheet("color: #4a6a8a; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        row.addWidget(lbl)
        row.addStretch()

        add_btn = QPushButton("+ Add")
        add_btn.setObjectName("addBtn")
        add_btn.clicked.connect(self.add_requested)
        row.addWidget(add_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("editBtn")
        edit_btn.clicked.connect(self._on_edit_clicked)
        row.addWidget(edit_btn)

        del_btn = QPushButton("Delete")
        del_btn.setObjectName("deleteBtn")
        del_btn.clicked.connect(self._on_delete_clicked)
        row.addWidget(del_btn)

        return bar

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def populate(self, activities: Dict[str, Activity]):
        """Refresh table with the given activities dict."""
        self._activities = activities
        self.table.setRowCount(0)

        for act in activities.values():
            self._append_row(act)

    def _append_row(self, act: Activity):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setRowHeight(row, 28)

        is_critical = act.is_critical
        bg = CLR_CRITICAL if is_critical else (CLR_ROW_EVEN if row % 2 == 0 else CLR_ROW_ODD)

        for col, attr in enumerate(COL_ATTRS):
            value = getattr(act, attr)

            # Format value for display
            if attr == "predecessors":
                text = ",".join(value) if isinstance(value, list) else str(value)
            elif attr == "is_critical":
                text = "★ YES" if value else ""
            else:
                text = str(value)

            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignCenter if col != 1 else Qt.AlignVCenter | Qt.AlignLeft)

            # Colours
            item.setBackground(QBrush(bg))
            if is_critical:
                item.setForeground(QBrush(CLR_CRITICAL_FG if attr == "is_critical" else CLR_TEXT))
            elif attr == "total_float" and act.total_float == 0 and act.EF > 0:
                item.setForeground(QBrush(CLR_FLOAT_ZERO))
            elif attr in ("ES", "EF", "LS", "LF", "total_float") and act.EF == 0:
                item.setForeground(QBrush(CLR_DIM))
            else:
                item.setForeground(QBrush(CLR_TEXT))

            item.setData(Qt.UserRole, act.id)  # store ID for lookup
            self.table.setItem(row, col, item)

    def selected_id(self) -> Optional[str]:
        selected = self.table.selectedItems()
        if selected:
            return selected[0].data(Qt.UserRole)
        return None

    # ------------------------------------------------------------------
    # Signals / slots
    # ------------------------------------------------------------------

    def _on_selection_changed(self):
        act_id = self.selected_id()
        if act_id:
            self.activity_selected.emit(act_id)

    def _on_double_click(self, index):
        act_id = self.selected_id()
        if act_id:
            self.edit_requested.emit(act_id)

    def _on_edit_clicked(self):
        act_id = self.selected_id()
        if act_id:
            self.edit_requested.emit(act_id)

    def _on_delete_clicked(self):
        act_id = self.selected_id()
        if act_id:
            self.delete_requested.emit(act_id)
