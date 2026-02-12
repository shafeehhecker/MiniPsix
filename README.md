# Mini-P6 — CPM Scheduler

A desktop Critical Path Method (CPM) scheduler built with Python + PySide6.
Inspired by Primavera P6, designed to be lean, clean, and educational.

---

## Features (Phase 1)

- **CPM Engine** — Forward pass, backward pass, float calculation, critical path identification
- **Activity Table** — P6-style grid with ES, EF, LS, LF, Float columns
- **Gantt Chart** — Auto-rendered from CPM results; critical path highlighted in red
- **SQLite persistence** — Activities saved automatically between sessions
- **Add / Edit / Delete** activities via dialog
- **Load Sample Project** — 5-activity demo network with a real critical path

---

## Install

```bash
pip install -r requirements.txt
```

> Requires Python 3.11+

---

## Run

```bash
python main.py
```

---

## How to Use

1. Click **Load Sample Project** to load the demo dataset
2. Click **▶ Schedule** to run the CPM engine
3. The table fills with ES/EF/LS/LF/Float values
4. The Gantt chart renders — red bars = critical path
5. Use **+ Add** to add your own activities
6. Double-click any row to edit it

---

## Project Structure

```
mini_p6/
├── main.py                  ← Entry point
├── engine/
│   ├── activity.py          ← Activity dataclass
│   └── scheduler.py         ← CPM engine (forward/backward pass)
├── database/
│   ├── models.py            ← SQLAlchemy models
│   └── db.py                ← CRUD operations
├── ui/
│   ├── main_window.py       ← Main application window
│   ├── activity_table.py    ← Activity grid widget
│   ├── gantt_view.py        ← Gantt chart (QGraphicsView)
│   ├── activity_dialog.py   ← Add/Edit dialog
│   └── status_panel.py      ← Bottom status bar
└── requirements.txt
```

---

## Sample Data

| ID | Name       | Dur | Predecessor |
|----|------------|-----|-------------|
| A  | Start      | 2   | —           |
| B  | Foundation | 4   | A           |
| C  | Structure  | 6   | B           |
| D  | Electrical | 3   | B           |
| E  | Finish     | 2   | C,D         |

**Critical path:** A → B → C → E (duration = 14 days)

---

## Phase 2 Ideas

- WBS tree panel
- Date-based scheduling (not just day offsets)
- Export to PDF / Excel
- Multiple calendars
- Resource loading
- P6 XML import/export
