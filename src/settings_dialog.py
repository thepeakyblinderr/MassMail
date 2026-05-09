import smtplib

import keyring
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout,
)

from .email_sender import SMTP_PROVIDERS

KEYRING_SERVICE = "MassMail"


# ------------------------------------------------------------------
# Credential helpers
# ------------------------------------------------------------------

def save_settings(sender_name: str, email: str, password: str, provider: str):
    keyring.set_password(KEYRING_SERVICE, "sender_name", sender_name)
    keyring.set_password(KEYRING_SERVICE, "email",       email)
    keyring.set_password(KEYRING_SERVICE, "password",    password)
    keyring.set_password(KEYRING_SERVICE, "provider",    provider)


def load_settings() -> dict:
    return {
        "sender_name": keyring.get_password(KEYRING_SERVICE, "sender_name") or "",
        "email":       keyring.get_password(KEYRING_SERVICE, "email")       or "",
        "password":    keyring.get_password(KEYRING_SERVICE, "password")    or "",
        "provider":    keyring.get_password(KEYRING_SERVICE, "provider")    or "Microsoft 365 / Outlook",
    }


def settings_complete() -> bool:
    s = load_settings()
    return bool(s["email"] and s["password"])


# ------------------------------------------------------------------
# Dialog
# ------------------------------------------------------------------

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Email Settings")
        self.setFixedWidth(460)
        self.setStyleSheet("""
            QDialog { background: #f9fafb; }
            QLabel  { color: #374151; font-size: 13px; }
            QLineEdit {
                border: 1px solid #d1d5db; border-radius: 6px;
                padding: 8px 10px; background: #ffffff;
                font-size: 13px; color: #1f2937;
            }
            QLineEdit:focus { border-color: #3b82f6; }
            QComboBox {
                border: 1px solid #d1d5db; border-radius: 6px;
                padding: 7px 10px; background: #ffffff;
                font-size: 13px; color: #1f2937;
            }
            QPushButton#save {
                background: #2563eb; color: #ffffff;
                border: none; border-radius: 7px;
                padding: 9px 24px; font-size: 13px; font-weight: bold;
            }
            QPushButton#save:hover { background: #1d4ed8; }
            QPushButton#test {
                background: #ffffff; color: #374151;
                border: 1px solid #d1d5db; border-radius: 7px;
                padding: 9px 18px; font-size: 13px;
            }
            QPushButton#test:hover { background: #f3f4f6; }
            QLabel#hint {
                color: #6b7280; font-size: 11px;
            }
            QLabel#section {
                font-weight: bold; color: #1e40af;
                font-size: 13px; padding-top: 6px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        # Title
        title = QLabel("⚙️  Email Settings")
        title.setStyleSheet("font-size:16px; font-weight:bold; color:#1e40af;")
        layout.addWidget(title)

        hint = QLabel("Your credentials are stored securely in Windows Credential Manager — never in any file.")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # Form
        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Rajesh Kumar")
        form.addRow("Your Name:", self.name_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("e.g. rajesh@company.com")
        form.addRow("Your Email:", self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Your email password or App Password")
        form.addRow("Password:", self.password_input)

        self.provider_combo = QComboBox()
        for p in SMTP_PROVIDERS:
            self.provider_combo.addItem(p)
        form.addRow("Provider:", self.provider_combo)

        layout.addLayout(form)

        # App password guide
        guide = QLabel(
            "💡 <b>How to get an App Password (recommended):</b><br>"
            "Go to <b>mysignins.microsoft.com</b> → Security → App passwords → New → Copy it here"
        )
        guide.setObjectName("hint")
        guide.setWordWrap(True)
        guide.setStyleSheet("background:#eff6ff; border:1px solid #bfdbfe; border-radius:6px; padding:8px; font-size:11px; color:#1e40af;")
        layout.addWidget(guide)

        # Buttons
        btn_row = QHBoxLayout()
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.setObjectName("test")
        self.test_btn.clicked.connect(self._test_connection)
        btn_row.addWidget(self.test_btn)

        btn_row.addStretch()

        save_btn = QPushButton("Save")
        save_btn.setObjectName("save")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

        # Load existing
        self._load()

    def _load(self):
        s = load_settings()
        self.name_input.setText(s["sender_name"])
        self.email_input.setText(s["email"])
        self.password_input.setText(s["password"])
        idx = self.provider_combo.findText(s["provider"])
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)

    def _save(self):
        name     = self.name_input.text().strip()
        email    = self.email_input.text().strip()
        password = self.password_input.text()
        provider = self.provider_combo.currentText()

        if not email or not password:
            QMessageBox.warning(self, "Missing Fields", "Please enter your email and password.")
            return

        save_settings(name, email, password, provider)
        QMessageBox.information(self, "Saved", "Settings saved successfully.")
        self.accept()

    def _test_connection(self):
        email    = self.email_input.text().strip()
        password = self.password_input.text()
        provider = self.provider_combo.currentText()

        if not email or not password:
            QMessageBox.warning(self, "Missing", "Enter email and password first.")
            return

        host, port = SMTP_PROVIDERS[provider]
        self.test_btn.setText("Testing…")
        self.test_btn.setEnabled(False)
        self.repaint()

        try:
            with smtplib.SMTP(host, port, timeout=15) as s:
                s.ehlo()
                s.starttls()
                s.ehlo()
                s.login(email, password)
            QMessageBox.information(self, "Success ✅", "Connected successfully! Your settings are working.")
        except smtplib.SMTPAuthenticationError:
            QMessageBox.critical(
                self, "Login Failed ❌",
                "Wrong email or password.\n\n"
                "Tip: Use an App Password instead of your main password.\n"
                "Go to mysignins.microsoft.com → Security → App passwords"
            )
        except Exception as e:
            QMessageBox.critical(self, "Connection Failed ❌", str(e))
        finally:
            self.test_btn.setText("Test Connection")
            self.test_btn.setEnabled(True)
