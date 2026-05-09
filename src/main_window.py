import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QMessageBox, QProgressBar, QPushButton, QScrollArea,
    QSizePolicy, QSplitter, QStatusBar, QToolButton,
    QVBoxLayout, QWidget,
)

from .editor import RichTextEditor
from .email_sender import EmailSenderThread, SMTP_PROVIDERS
from .excel_reader import load_vendors
from .preview_dialog import PreviewDialog
from .settings_dialog import SettingsDialog, load_settings, settings_complete
from .vendor_table import VendorTable

STYLE = """
QMainWindow, QWidget#root {
    background: #f3f4f6;
}
QLabel#header_title {
    font-size: 22px;
    font-weight: bold;
    color: #1e40af;
}
QLabel#header_sub {
    font-size: 12px;
    color: #6b7280;
}
QLabel.section_label {
    font-size: 11px;
    font-weight: bold;
    color: #6b7280;
    letter-spacing: 1px;
    text-transform: uppercase;
}
QLineEdit {
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 8px 10px;
    background: #ffffff;
    font-size: 13px;
    color: #1f2937;
}
QLineEdit:focus { border-color: #3b82f6; }
QPushButton#primary {
    background: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton#primary:hover { background: #1d4ed8; }
QPushButton#primary:disabled { background: #93c5fd; }
QPushButton#secondary {
    background: #ffffff;
    color: #374151;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
}
QPushButton#secondary:hover { background: #f9fafb; }
QPushButton#danger {
    background: #dc2626;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
}
QPushButton#danger:hover { background: #b91c1c; }
QPushButton#upload_btn {
    background: #eff6ff;
    color: #1d4ed8;
    border: 2px dashed #93c5fd;
    border-radius: 8px;
    padding: 12px;
    font-size: 13px;
}
QPushButton#upload_btn:hover { background: #dbeafe; }
QFrame#card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
}
QProgressBar {
    border: none;
    border-radius: 6px;
    background: #e5e7eb;
    height: 12px;
    text-align: center;
    font-size: 11px;
    color: #374151;
}
QProgressBar::chunk {
    border-radius: 6px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #3b82f6, stop:1 #2563eb);
}
QListWidget {
    border: 1px solid #d1d5db;
    border-radius: 6px;
    background: #ffffff;
    font-size: 13px;
}
QListWidget::item { padding: 4px 8px; }
QListWidget::item:selected { background: #eff6ff; color: #1d4ed8; }
"""


def _card(parent=None) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame(parent)
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(8)
    return frame, layout


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setProperty("class", "section_label")
    lbl.setStyleSheet("font-size:11px; font-weight:bold; color:#6b7280; letter-spacing:1px;")
    return lbl


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MassMail")
        self.resize(1100, 780)
        self.setStyleSheet(STYLE)

        self.vendors: list[dict] = []
        self.attachments: list[str] = []
        self.sender_thread: EmailSenderThread | None = None

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(12)

        main_layout.addWidget(self._build_header())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setSizes([360, 700])
        splitter.setHandleWidth(6)
        main_layout.addWidget(splitter, 1)

        main_layout.addWidget(self._build_progress_bar())
        main_layout.addWidget(self._build_action_bar())

        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("font-size:12px; color:#6b7280;")
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready — upload an Excel file to get started.")

    # ------------------------------------------------------------------
    # UI builders
    # ------------------------------------------------------------------

    def _build_header(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background:#1e40af; border-radius:10px;")
        h = QHBoxLayout(w)
        h.setContentsMargins(18, 12, 18, 12)

        left = QVBoxLayout()
        title = QLabel("MassMail")
        title.setObjectName("header_title")
        title.setStyleSheet("font-size:22px; font-weight:bold; color:#ffffff;")
        sub = QLabel("Send personalised bulk emails to all your vendors — no Outlook needed")
        sub.setStyleSheet("font-size:12px; color:#bfdbfe;")
        left.addWidget(title)
        left.addWidget(sub)
        h.addLayout(left, 1)

        self.vendor_count_badge = QLabel("0 vendors")
        self.vendor_count_badge.setStyleSheet(
            "background:#1d4ed8; color:#ffffff; border-radius:12px; padding:4px 14px; font-size:13px;"
        )
        h.addWidget(self.vendor_count_badge)

        settings_btn = QPushButton("⚙️  Settings")
        settings_btn.setStyleSheet(
            "background:#1d4ed8; color:#ffffff; border:1px solid #93c5fd;"
            "border-radius:8px; padding:6px 14px; font-size:13px;"
        )
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.clicked.connect(self._open_settings)
        h.addWidget(settings_btn)
        return w

    def _build_left_panel(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(10)

        # Upload card
        upload_card, ul = _card()
        ul.addWidget(_section_label("RECIPIENTS"))
        upload_btn = QPushButton("📂  Upload Excel (.xlsx)")
        upload_btn.setObjectName("upload_btn")
        upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        upload_btn.clicked.connect(self._upload_excel)
        ul.addWidget(upload_btn)

        hint = QLabel("Excel must have columns: <b>Name</b> and <b>Email</b>")
        hint.setStyleSheet("font-size:11px; color:#9ca3af;")
        hint.setWordWrap(True)
        ul.addWidget(hint)
        layout.addWidget(upload_card)

        # Vendor table card
        table_card, tl = _card()
        tl.setContentsMargins(8, 8, 8, 8)
        self.vendor_table = VendorTable()
        tl.addWidget(self.vendor_table)
        layout.addWidget(table_card, 1)

        return w

    def _build_right_panel(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background:transparent;")

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(6, 0, 0, 0)
        layout.setSpacing(10)

        # Subject card
        subj_card, sl = _card()
        sl.addWidget(_section_label("SUBJECT"))
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("e.g. Contract Update Q2 2026 — {{Name}}")
        sl.addWidget(self.subject_input)
        layout.addWidget(subj_card)

        # Body card
        body_card, bl = _card()
        bl.addWidget(_section_label("EMAIL BODY"))
        self.editor = RichTextEditor()
        bl.addWidget(self.editor)
        layout.addWidget(body_card)

        # Attachments card
        att_card, al = _card()
        al.addWidget(_section_label("PDF ATTACHMENTS"))
        add_pdf_btn = QPushButton("📎  Add PDF(s)")
        add_pdf_btn.setObjectName("secondary")
        add_pdf_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_pdf_btn.clicked.connect(self._add_pdfs)
        al.addWidget(add_pdf_btn)
        self.attachment_list = QListWidget()
        self.attachment_list.setMaximumHeight(110)
        al.addWidget(self.attachment_list)
        layout.addWidget(att_card)

        layout.addStretch()
        scroll.setWidget(inner)
        return scroll

    def _build_progress_bar(self) -> QWidget:
        self.progress_widget = QWidget()
        self.progress_widget.setVisible(False)
        pl = QVBoxLayout(self.progress_widget)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(4)

        self.progress_label = QLabel("Preparing…")
        self.progress_label.setStyleSheet("font-size:12px; color:#374151;")
        pl.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        pl.addWidget(self.progress_bar)
        return self.progress_widget

    def _build_action_bar(self) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(10)

        self.preview_btn = QPushButton("👁  Preview Email")
        self.preview_btn.setObjectName("secondary")
        self.preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preview_btn.clicked.connect(self._preview_email)
        h.addWidget(self.preview_btn)

        h.addStretch()

        self.stop_btn = QPushButton("⏹  Stop")
        self.stop_btn.setObjectName("danger")
        self.stop_btn.setVisible(False)
        self.stop_btn.clicked.connect(self._stop_sending)
        h.addWidget(self.stop_btn)

        self.send_btn = QPushButton("🚀  Send to All Vendors")
        self.send_btn.setObjectName("primary")
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.clicked.connect(self._send_emails)
        h.addWidget(self.send_btn)

        return w

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _upload_excel(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Excel File", "", "Excel Files (*.xlsx *.xls)"
        )
        if not path:
            return
        vendors, error = load_vendors(path)
        if error:
            QMessageBox.warning(self, "Excel Error", error)
            return
        self.vendors = vendors
        self.vendor_table.load_vendors(vendors)
        self.vendor_count_badge.setText(f"{len(vendors)} vendors")
        self.status_bar.showMessage(f"Loaded {len(vendors)} vendors from {os.path.basename(path)}")

    def _add_pdfs(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF Files", "", "PDF Files (*.pdf)"
        )
        for path in paths:
            if path not in self.attachments:
                self.attachments.append(path)
                item = QListWidgetItem(f"📄  {os.path.basename(path)}")
                item.setToolTip(path)
                self.attachment_list.addItem(item)

    def _preview_email(self):
        if not self.vendors:
            QMessageBox.information(self, "No Vendors", "Please upload an Excel file first.")
            return
        subject = self.subject_input.text().strip() or "(no subject)"
        html = self.editor.toHtml()
        dlg = PreviewDialog(self.vendors, subject, html, self)
        dlg.exec()

    def _open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    def _send_emails(self):
        if not self.vendors:
            QMessageBox.warning(self, "No Vendors", "Please upload an Excel file first.")
            return
        subject = self.subject_input.text().strip()
        if not subject:
            QMessageBox.warning(self, "No Subject", "Please enter a subject line.")
            return
        html = self.editor.toHtml()
        if not html.strip() or "<body></body>" in html:
            QMessageBox.warning(self, "Empty Body", "Please compose an email body.")
            return

        if not settings_complete():
            QMessageBox.warning(
                self, "Settings Required",
                "Please configure your email settings first.\n\nClick the ⚙️ Settings button."
            )
            self._open_settings()
            return

        s = load_settings()
        host, port = SMTP_PROVIDERS[s["provider"]]

        reply = QMessageBox.question(
            self, "Confirm Send",
            f"Send email to <b>{len(self.vendors)}</b> vendors?<br><br>"
            f"From: <i>{s['email']}</i><br>"
            f"Subject: <i>{subject}</i>",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.vendor_table.reset_all_statuses()
        self._set_sending_ui(True)
        self.progress_bar.setMaximum(len(self.vendors))
        self.progress_bar.setValue(0)
        self._sent = 0
        self._failed = 0

        self.sender_thread = EmailSenderThread(
            self.vendors, subject, html, self.attachments,
            smtp_host=host, smtp_port=port,
            email=s["email"], password=s["password"],
            sender_name=s["sender_name"] or s["email"],
        )
        self.sender_thread.progress.connect(self._on_progress)
        self.sender_thread.finished.connect(self._on_finished)
        self.sender_thread.error.connect(self._on_error)
        self.sender_thread.start()

    def _stop_sending(self):
        if self.sender_thread:
            self.sender_thread.stop()
            self.status_bar.showMessage("Stopping after current email…")

    # ------------------------------------------------------------------
    # Thread callbacks
    # ------------------------------------------------------------------

    def _on_progress(self, index: int, status: str, detail: str):
        self.vendor_table.set_status(index, status)
        self.vendor_table.scrollToItem(self.vendor_table.item(index, 2))
        if status == "Sent":
            self._sent += 1
        else:
            self._failed += 1
        done = self._sent + self._failed
        self.progress_bar.setValue(done)
        self.progress_label.setText(
            f"Sending… {done} / {len(self.vendors)}  "
            f"✅ {self._sent} sent   ❌ {self._failed} failed"
        )
        self.status_bar.showMessage(
            f"Sent: {self._sent}  Failed: {self._failed}  Remaining: {len(self.vendors) - done}"
        )

    def _on_finished(self, sent: int, failed: int):
        self._set_sending_ui(False)
        msg = f"Done!  ✅ {sent} sent   ❌ {failed} failed"
        self.progress_label.setText(msg)
        self.status_bar.showMessage(msg)
        QMessageBox.information(
            self, "Sending Complete",
            f"<b>Sending complete!</b><br><br>"
            f"✅ Sent: {sent}<br>"
            f"❌ Failed: {failed}"
        )

    def _on_error(self, message: str):
        self._set_sending_ui(False)
        QMessageBox.critical(self, "Outlook Error", message)
        self.status_bar.showMessage("Error — could not connect to Outlook.")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_sending_ui(self, sending: bool):
        self.send_btn.setVisible(not sending)
        self.stop_btn.setVisible(sending)
        self.progress_widget.setVisible(sending or self._sent + self._failed > 0 if hasattr(self, "_sent") else sending)
        self.preview_btn.setEnabled(not sending)
