"""
Gantt Chart widget.
Draws horizontal Gantt bars on a QGraphicsScene with:
  - Timeline header
  - Activity bars (colour-coded: critical = red, normal = steel blue)
  - Float bars (greyed)
  - Activity name labels on bars
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsLineItem, QFrame, QLabel,
    QSizePolicy
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import (
    QColor, QBrush, QPen, QFont, QPainter, QLinearGradient
)
from typing import Dict

from activity import Activity


# Layout constants
ROW_H       = 32      # height of each Gantt row (pixels)
ROW_PAD     = 4       # vertical padding inside row
LABEL_W     = 160     # left column (activity name)
DAY_W       = 28      # pixels per day
HEADER_H    = 36      # height of timeline header
MIN_DAYS    = 20      # minimum timeline width (days)

# Colours
CLR_BG          = "#1e2530"
CLR_HEADER_BG   = "#151c26"
CLR_HEADER_FG   = "#4a6a8a"
CLR_GRID        = "#232e3c"
CLR_LABEL_FG    = "#8aa8c0"
CLR_BAR_NORMAL  = "#2a6090"
CLR_BAR_CRIT    = "#9e2a30"
CLR_BAR_FLOAT   = "#253040"
CLR_BAR_CRIT_BORDER  = "#e04050"
CLR_BAR_NRM_BORDER   = "#4090c0"
CLR_BAR_TEXT    = "#e0eefa"
CLR_TODAY_LINE  = "#e8b840"
CLR_ROW_EVEN    = "#1a2230"
CLR_ROW_ODD     = "#1e2838"


class GanttView(QWidget):
    """Gantt Chart panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._activities: Dict[str, Activity] = {}
        self._setup_ui()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_ui(self):
        self.setStyleSheet(f"background-color: {CLR_BG};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar strip
        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            QFrame {{ background-color: {CLR_HEADER_BG}; border-bottom: 1px solid #2a3545; }}
            QLabel {{ color: #4a6a8a; font-size: 10px; font-weight: bold; letter-spacing: 1px; }}
        """)
        tb_row = QHBoxLayout(toolbar)
        tb_row.setContentsMargins(12, 7, 12, 7)
        lbl = QLabel("GANTT CHART")
        tb_row.addWidget(lbl)
        tb_row.addStretch()
        legend_crit = QLabel("■ Critical Path")
        legend_crit.setStyleSheet(f"color: {CLR_BAR_CRIT_BORDER}; font-size: 11px;")
        tb_row.addWidget(legend_crit)
        legend_norm = QLabel("■ Normal")
        legend_norm.setStyleSheet(f"color: {CLR_BAR_NRM_BORDER}; font-size: 11px; margin-left: 10px;")
        tb_row.addWidget(legend_norm)
        layout.addWidget(toolbar)

        # Graphics view
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing, True)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setStyleSheet(f"""
            QGraphicsView {{
                background-color: {CLR_BG};
                border: none;
            }}
            QScrollBar:horizontal, QScrollBar:vertical {{
                background: #1a2230;
                height: 10px; width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:horizontal, QScrollBar::handle:vertical {{
                background: #3a4a5a;
                border-radius: 5px;
            }}
        """)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        layout.addWidget(self.view)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render_gantt(self, activities: Dict[str, Activity]):
        """Rebuild the entire scene from the activities dict."""
        self._activities = activities
        self.scene.clear()

        if not activities:
            self._draw_empty_state()
            return

        # Determine project span
        project_end = max(
            (a.EF for a in activities.values() if a.EF > 0),
            default=MIN_DAYS
        )
        total_days = max(project_end + 2, MIN_DAYS)

        scene_w = LABEL_W + total_days * DAY_W + 20
        scene_h = HEADER_H + len(activities) * ROW_H + 10
        self.scene.setSceneRect(0, 0, scene_w, scene_h)

        self._draw_background(total_days, len(activities))
        self._draw_header(total_days)
        self._draw_bars(activities, total_days)

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_empty_state(self):
        self.scene.setSceneRect(0, 0, 600, 200)
        msg = QGraphicsTextItem("No scheduled data.\nAdd activities and click  ▶ Schedule  to compute the CPM.")
        msg.setDefaultTextColor(QColor("#3a5070"))
        font = QFont("Consolas", 12)
        msg.setFont(font)
        msg.setPos(80, 70)
        self.scene.addItem(msg)

    def _draw_background(self, total_days: int, row_count: int):
        # Left label column background
        label_rect = QGraphicsRectItem(0, HEADER_H, LABEL_W, row_count * ROW_H)
        label_rect.setBrush(QBrush(QColor("#161e28")))
        label_rect.setPen(QPen(Qt.NoPen))
        self.scene.addItem(label_rect)

        # Row stripes
        for r in range(row_count):
            y = HEADER_H + r * ROW_H
            clr = CLR_ROW_EVEN if r % 2 == 0 else CLR_ROW_ODD
            stripe = QGraphicsRectItem(LABEL_W, y, total_days * DAY_W, ROW_H)
            stripe.setBrush(QBrush(QColor(clr)))
            stripe.setPen(QPen(Qt.NoPen))
            self.scene.addItem(stripe)

        # Vertical grid lines (every 5 days)
        pen_grid = QPen(QColor(CLR_GRID), 1, Qt.DotLine)
        for d in range(0, total_days + 1, 5):
            x = LABEL_W + d * DAY_W
            line = QGraphicsLineItem(x, HEADER_H, x, HEADER_H + row_count * ROW_H)
            line.setPen(pen_grid)
            self.scene.addItem(line)

        # Horizontal row dividers
        pen_div = QPen(QColor("#222d3c"), 1)
        for r in range(row_count + 1):
            y = HEADER_H + r * ROW_H
            divider = QGraphicsLineItem(0, y, LABEL_W + total_days * DAY_W, y)
            divider.setPen(pen_div)
            self.scene.addItem(divider)

    def _draw_header(self, total_days: int):
        # Header background
        hdr_rect = QGraphicsRectItem(0, 0, LABEL_W + total_days * DAY_W + 20, HEADER_H)
        hdr_rect.setBrush(QBrush(QColor(CLR_HEADER_BG)))
        hdr_rect.setPen(QPen(Qt.NoPen))
        self.scene.addItem(hdr_rect)

        # "Activity" label in header
        act_lbl = QGraphicsTextItem("Activity")
        act_lbl.setDefaultTextColor(QColor(CLR_HEADER_FG))
        act_lbl.setFont(QFont("Arial", 9, QFont.Bold))
        act_lbl.setPos(10, 8)
        self.scene.addItem(act_lbl)

        # Day numbers
        font_day = QFont("Consolas", 9)
        pen_hdr_line = QPen(QColor("#2a3a4a"), 1)

        for d in range(0, total_days + 1, 5):
            x = LABEL_W + d * DAY_W
            # Tick line
            tick = QGraphicsLineItem(x, HEADER_H - 10, x, HEADER_H)
            tick.setPen(pen_hdr_line)
            self.scene.addItem(tick)

            # Day label
            lbl = QGraphicsTextItem(f"D{d}")
            lbl.setDefaultTextColor(QColor(CLR_HEADER_FG))
            lbl.setFont(font_day)
            lbl.setPos(x - 10, 6)
            self.scene.addItem(lbl)

        # Header bottom border
        hdr_line = QGraphicsLineItem(0, HEADER_H, LABEL_W + total_days * DAY_W + 20, HEADER_H)
        hdr_line.setPen(QPen(QColor("#2a3a4a"), 2))
        self.scene.addItem(hdr_line)

    def _draw_bars(self, activities: Dict[str, Activity], total_days: int):
        font_bar = QFont("Arial", 9)
        font_lbl = QFont("Arial", 10)
        pen_none = QPen(Qt.NoPen)

        for row_idx, (act_id, act) in enumerate(activities.items()):
            y = HEADER_H + row_idx * ROW_H
            bar_y = y + ROW_PAD
            bar_h = ROW_H - ROW_PAD * 2

            # ---- Activity name label (left column) ----
            lbl = QGraphicsTextItem(f"  {act.id}  {act.name}")
            lbl.setDefaultTextColor(QColor("#c8d8e8") if act.is_critical else QColor(CLR_LABEL_FG))
            lbl.setFont(font_lbl)
            lbl.setPos(4, y + (ROW_H - 16) // 2)
            # Clip to label column
            lbl.setTextWidth(LABEL_W - 8)
            self.scene.addItem(lbl)

            # Skip bars if not yet scheduled (EF == 0)
            if act.EF == 0 and act.ES == 0 and act.duration > 0 and act.LF == 0:
                continue

            # ---- Float bar (LS → LF, faded) ----
            if act.total_float > 0:
                fx = LABEL_W + act.LS * DAY_W
                fw = act.total_float * DAY_W
                float_bar = QGraphicsRectItem(fx, bar_y + 6, fw, bar_h - 12)
                float_bar.setBrush(QBrush(QColor(CLR_BAR_FLOAT)))
                float_bar.setPen(QPen(QColor("#2e3e50"), 1))
                float_bar.setZValue(1)
                self.scene.addItem(float_bar)

            # ---- Activity bar (ES → EF) ----
            bx = LABEL_W + act.ES * DAY_W
            bw = max(act.duration * DAY_W, 2)

            if act.is_critical:
                bar_color   = QColor(CLR_BAR_CRIT)
                border_color = QColor(CLR_BAR_CRIT_BORDER)
            else:
                bar_color   = QColor(CLR_BAR_NORMAL)
                border_color = QColor(CLR_BAR_NRM_BORDER)

            bar_rect = QGraphicsRectItem(bx, bar_y, bw, bar_h)
            bar_rect.setBrush(QBrush(bar_color))
            bar_rect.setPen(QPen(border_color, 1.5))
            bar_rect.setZValue(2)
            self.scene.addItem(bar_rect)

            # ---- Bar label (duration text) ----
            if bw > 24:
                bar_txt = QGraphicsTextItem(f"{act.duration}d")
                bar_txt.setDefaultTextColor(QColor(CLR_BAR_TEXT))
                bar_txt.setFont(font_bar)
                bar_txt.setPos(bx + 4, bar_y + 4)
                bar_txt.setZValue(3)
                self.scene.addItem(bar_txt)

        # Vertical line at day 0
        d0_line = QGraphicsLineItem(LABEL_W, 0, LABEL_W, HEADER_H + len(activities) * ROW_H)
        d0_line.setPen(QPen(QColor("#2a3a4a"), 2))
        self.scene.addItem(d0_line)
