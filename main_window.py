"""
Main Window for Mini-P6 CPM Scheduler.
Layout:
  ┌─────────────────────────────────────────────────────┐
  │  Toolbar (Schedule button, Load sample, etc.)       │
  ├──────────────────────┬──────────────────────────────┤
  │   Activity Table     │     Gantt Chart              │
  │   (left 45%)         │     (right 55%)              │
  ├──────────────────────┴──────────────────────────────┤
  │  Status Panel                                       │
  └─────────────────────────────────────────────────────┘
"""
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QPushButton, QLabel, QFrame,
    QMessageBox, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon, QColor, QPalette

from activity import Activity
from scheduler import CPMScheduler, SchedulerError
from db import (
    init_db, load_all_activities, save_activity,
    save_all_activities, delete_activity, activity_id_exists
)
from activity_table import ActivityTable
from gantt_view import GanttView
from activity_dialog import ActivityDialog
from status_panel import StatusPanel
from typing import Dict


SAMPLE_ACTIVITIES = [
    Activity("A", "Start",      2, []),
    Activity("B", "Foundation", 4, ["A"]),
    Activity("C", "Structure",  6, ["B"]),
    Activity("D", "Electrical", 3, ["B"]),
    Activity("E", "Finish",     2, ["C", "D"]),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._activities: Dict[str, Activity] = {}
        init_db()
        self._setup_window()
        self._setup_ui()
        self._load_from_db()

    # ------------------------------------------------------------------
    # Window setup
    # ------------------------------------------------------------------

    def _setup_window(self):
        self.setWindowTitle("Mini-P6  |  CPM Scheduler")
        self.setMinimumSize(1100, 680)
        self.resize(1400, 780)

        # Apply global dark palette
        palette = QPalette()
        palette.setColor(QPalette.Window,          QColor("#1e2530"))
        palette.setColor(QPalette.WindowText,      QColor("#c8d8e8"))
        palette.setColor(QPalette.Base,            QColor("#161e2a"))
        palette.setColor(QPalette.AlternateBase,   QColor("#1a2230"))
        palette.setColor(QPalette.Text,            QColor("#c8d8e8"))
        palette.setColor(QPalette.Button,          QColor("#252d3a"))
        palette.setColor(QPalette.ButtonText,      QColor("#c0ccd8"))
        palette.setColor(QPalette.Highlight,       QColor("#1e4a6a"))
        palette.setColor(QPalette.HighlightedText, QColor("#e0f0ff"))
        QApplication.setPalette(palette)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 1. Title bar
        root.addWidget(self._build_titlebar())

        # 2. Toolbar
        root.addWidget(self._build_toolbar())

        # 3. Main content split
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #2a3545;
                width: 2px;
            }
        """)

        self.activity_table = ActivityTable()
        self.activity_table.add_requested.connect(self._on_add_activity)
        self.activity_table.edit_requested.connect(self._on_edit_activity)
        self.activity_table.delete_requested.connect(self._on_delete_activity)

        self.gantt_view = GanttView()

        splitter.addWidget(self.activity_table)
        splitter.addWidget(self.gantt_view)
        splitter.setSizes([480, 720])
        root.addWidget(splitter)

        # 4. Status bar
        self.status_panel = StatusPanel()
        root.addWidget(self.status_panel)

    def _build_titlebar(self) -> QWidget:
        bar = QFrame()
        bar.setStyleSheet("""
            QFrame {
                background-color: #0f1620;
                border-bottom: 2px solid #1e3a52;
            }
        """)
        bar.setFixedHeight(46)
        row = QHBoxLayout(bar)
        row.setContentsMargins(16, 0, 16, 0)

        # Logo / title
        logo = QLabel("◈")
        logo.setStyleSheet("color: #2a7ab0; font-size: 20px;")
        row.addWidget(logo)

        title = QLabel("Mini-P6")
        title.setStyleSheet("color: #90b8d8; font-size: 18px; font-weight: bold; letter-spacing: 1px; margin-left: 6px;")
        row.addWidget(title)

        sub = QLabel("CPM Scheduler")
        sub.setStyleSheet("color: #3a5a78; font-size: 12px; margin-left: 4px; margin-top: 4px;")
        row.addWidget(sub)

        row.addStretch()

        help_lbl = QLabel("Double-click a row to edit  •  Drag splitter to resize")
        help_lbl.setStyleSheet("color: #2a4a62; font-size: 11px;")
        row.addWidget(help_lbl)

        return bar

    def _build_toolbar(self) -> QWidget:
        bar = QFrame()
        bar.setStyleSheet("""
            QFrame {
                background-color: #161e2a;
                border-bottom: 1px solid #2a3545;
            }
            QPushButton {
                background-color: #1e2d3e;
                color: #7090a8;
                border: 1px solid #2a3a4a;
                border-radius: 4px;
                padding: 6px 18px;
                font-size: 12px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #253545;
                color: #90b8d8;
            }
            QPushButton#scheduleBtn {
                background-color: #1a4a70;
                color: #78c8f8;
                border: 1px solid #2a6a98;
                font-weight: bold;
                font-size: 13px;
                padding: 6px 24px;
            }
            QPushButton#scheduleBtn:hover {
                background-color: #206090;
                color: #a8e0ff;
            }
            QPushButton#clearBtn:hover {
                background-color: #3d1e22;
                color: #e05060;
                border-color: #6a2030;
            }
        """)
        bar.setFixedHeight(48)

        row = QHBoxLayout(bar)
        row.setContentsMargins(12, 6, 12, 6)
        row.setSpacing(10)

        # Sample data button
        sample_btn = QPushButton("Load Sample Project")
        sample_btn.clicked.connect(self._load_sample)
        row.addWidget(sample_btn)

        # Clear button
        clear_btn = QPushButton("Clear All")
        clear_btn.setObjectName("clearBtn")
        clear_btn.clicked.connect(self._clear_all)
        row.addWidget(clear_btn)

        row.addStretch()

        # Schedule button (hero action)
        schedule_btn = QPushButton("▶  Schedule")
        schedule_btn.setObjectName("scheduleBtn")
        schedule_btn.setToolTip("Run CPM forward/backward pass and update Gantt")
        schedule_btn.clicked.connect(self._run_schedule)
        row.addWidget(schedule_btn)

        return bar

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_from_db(self):
        self._activities = load_all_activities()
        self._refresh_ui()
        if self._activities:
            self.status_panel.set_message(
                f"Loaded {len(self._activities)} activit(ies) from database."
            )

    def _refresh_ui(self):
        self.activity_table.populate(self._activities)
        self.gantt_view.render_gantt(self._activities)

    # ------------------------------------------------------------------
    # Toolbar actions
    # ------------------------------------------------------------------

    def _load_sample(self):
        reply = QMessageBox.question(
            self, "Load Sample",
            "This will replace the current project with sample data.\nContinue?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # Clear DB
        for act_id in list(self._activities.keys()):
            delete_activity(act_id)
        self._activities.clear()

        # Insert sample
        for act in SAMPLE_ACTIVITIES:
            a = Activity(act.id, act.name, act.duration, list(act.predecessors))
            self._activities[a.id] = a
            save_activity(a)

        self._refresh_ui()
        self.status_panel.set_message("Sample project loaded. Click ▶ Schedule to compute CPM.")

    def _clear_all(self):
        if not self._activities:
            return
        reply = QMessageBox.question(
            self, "Clear All",
            "Delete all activities? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        for act_id in list(self._activities.keys()):
            delete_activity(act_id)
        self._activities.clear()
        self._refresh_ui()
        self.status_panel.set_message("All activities cleared.")

    def _run_schedule(self):
        if not self._activities:
            self.status_panel.set_message("No activities to schedule.", error=True)
            return

        try:
            scheduler = CPMScheduler(self._activities)
            scheduler.schedule()
            # Results are written back into the same Activity objects
            save_all_activities(self._activities)
            critical = scheduler.get_critical_path()
            self._refresh_ui()
            self.status_panel.update_stats(self._activities, critical)
        except SchedulerError as e:
            self.status_panel.set_message(str(e), error=True)
            QMessageBox.critical(self, "Scheduling Error", str(e))

    # ------------------------------------------------------------------
    # Activity CRUD (from table signals)
    # ------------------------------------------------------------------

    def _on_add_activity(self):
        dlg = ActivityDialog(
            parent=self,
            existing_ids=list(self._activities.keys())
        )
        if dlg.exec():
            act = dlg.get_activity()
            self._activities[act.id] = act
            save_activity(act)
            self._refresh_ui()
            self.status_panel.set_message(
                f"Activity '{act.id}' added. Click ▶ Schedule to update CPM."
            )

    def _on_edit_activity(self, act_id: str):
        if act_id not in self._activities:
            return
        dlg = ActivityDialog(
            parent=self,
            activity=self._activities[act_id],
            existing_ids=list(self._activities.keys())
        )
        if dlg.exec():
            updated = dlg.get_activity()
            self._activities[act_id] = updated
            save_activity(updated)
            self._refresh_ui()
            self.status_panel.set_message(
                f"Activity '{act_id}' updated. Click ▶ Schedule to update CPM."
            )

    def _on_delete_activity(self, act_id: str):
        reply = QMessageBox.question(
            self, "Delete Activity",
            f"Delete activity '{act_id}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        del self._activities[act_id]
        delete_activity(act_id)
        self._refresh_ui()
        self.status_panel.set_message(
            f"Activity '{act_id}' deleted. Click ▶ Schedule to update CPM."
        )
