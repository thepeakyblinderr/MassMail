from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem


STATUS_COLORS = {
    "Pending": ("#6b7280", "#f9fafb"),   # gray text, light bg
    "Sending": ("#1d4ed8", "#dbeafe"),   # blue
    "Sent":    ("#15803d", "#dcfce7"),   # green
    "Failed":  ("#b91c1c", "#fee2e2"),   # red
}


class VendorTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(0, 3, parent)
        self.setHorizontalHeaderLabels(["Name", "Email", "Status"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(2, 90)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        self.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                background: #ffffff;
                alternate-background-color: #f9fafb;
                gridline-color: #f3f4f6;
                font-size: 13px;
                color: #1f2937;
            }
            QHeaderView::section {
                background: #f3f4f6;
                border: none;
                border-bottom: 2px solid #e5e7eb;
                padding: 6px 8px;
                font-weight: bold;
                color: #374151;
            }
            QTableWidget::item { padding: 4px 8px; color: #1f2937; }
            QTableWidget::item:selected { background: #eff6ff; color: #1d4ed8; }
        """)

    def load_vendors(self, vendors: list[dict]):
        self.setRowCount(0)
        for vendor in vendors:
            self._add_row(vendor["name"], vendor["email"], "Pending")

    def _add_row(self, name: str, email: str, status: str):
        row = self.rowCount()
        self.insertRow(row)
        for col, text in enumerate([name, email]):
            item = QTableWidgetItem(text)
            item.setForeground(QColor("#1f2937"))
            item.setBackground(QColor("#ffffff"))
            self.setItem(row, col, item)
        self._set_status_cell(row, status)

    def set_status(self, row: int, status: str):
        self._set_status_cell(row, status)

    def _set_status_cell(self, row: int, status: str):
        item = QTableWidgetItem(status)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        fg, bg = STATUS_COLORS.get(status, ("#374151", "#ffffff"))
        item.setForeground(QColor(fg))
        item.setBackground(QColor(bg))
        self.setItem(row, 2, item)

    def reset_all_statuses(self):
        for row in range(self.rowCount()):
            self._set_status_cell(row, "Pending")
