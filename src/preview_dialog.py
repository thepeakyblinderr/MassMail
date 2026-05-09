from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton,
    QTextBrowser, QVBoxLayout,
)


class PreviewDialog(QDialog):
    """
    Shows the composed email as it will look for each vendor.
    User can page through vendors with Prev / Next buttons.
    """

    def __init__(self, vendors: list[dict], subject: str, html_body: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Email Preview")
        self.resize(700, 560)
        self.vendors = vendors
        self.subject = subject
        self.html_body = html_body
        self.current = 0

        self.setStyleSheet("""
            QDialog { background: #f9fafb; }
            QLabel { color: #374151; font-size: 13px; }
            QPushButton {
                background: #2563eb; color: #ffffff;
                border: none; border-radius: 6px;
                padding: 7px 18px; font-size: 13px;
            }
            QPushButton:hover { background: #1d4ed8; }
            QPushButton:disabled { background: #93c5fd; }
            QPushButton#close_btn { background: #6b7280; }
            QPushButton#close_btn:hover { background: #4b5563; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header meta
        self.meta_label = QLabel()
        self.meta_label.setWordWrap(True)
        self.meta_label.setStyleSheet(
            "background:#ffffff; border:1px solid #e5e7eb; border-radius:6px; padding:10px;"
        )
        layout.addWidget(self.meta_label)

        # Body preview
        self.browser = QTextBrowser()
        self.browser.setOpenLinks(False)
        self.browser.setStyleSheet(
            "background:#ffffff; border:1px solid #e5e7eb; border-radius:6px; padding:10px;"
        )
        layout.addWidget(self.browser)

        # Navigation
        nav = QHBoxLayout()
        self.prev_btn = QPushButton("← Prev Vendor")
        self.prev_btn.clicked.connect(self._go_prev)
        nav.addWidget(self.prev_btn)

        self.counter_label = QLabel()
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav.addWidget(self.counter_label, 1)

        self.next_btn = QPushButton("Next Vendor →")
        self.next_btn.clicked.connect(self._go_next)
        nav.addWidget(self.next_btn)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("close_btn")
        close_btn.clicked.connect(self.accept)
        nav.addWidget(close_btn)

        layout.addLayout(nav)
        self._render()

    def _render(self):
        vendor = self.vendors[self.current]
        name = vendor["name"]
        email = vendor["email"]

        subject = self.subject.replace("{{Name}}", name)
        body = self.html_body.replace("{{Name}}", name)

        self.meta_label.setText(
            f"<b>To:</b> {email} &nbsp;&nbsp; <b>Subject:</b> {subject}"
        )
        self.browser.setHtml(body)

        total = len(self.vendors)
        self.counter_label.setText(f"{self.current + 1} / {total}")
        self.prev_btn.setEnabled(self.current > 0)
        self.next_btn.setEnabled(self.current < total - 1)

    def _go_prev(self):
        if self.current > 0:
            self.current -= 1
            self._render()

    def _go_next(self):
        if self.current < len(self.vendors) - 1:
            self.current += 1
            self._render()
