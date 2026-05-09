import base64
import os
import re
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from PyQt6.QtCore import QThread, pyqtSignal

SMTP_PROVIDERS = {
    "Microsoft 365 / Outlook": ("smtp.office365.com", 587),
    "Gmail":                   ("smtp.gmail.com",      587),
    "Yahoo":                   ("smtp.mail.yahoo.com", 587),
}


class EmailSenderThread(QThread):
    progress = pyqtSignal(int, str, str)   # index, "Sent"/"Failed", detail
    finished = pyqtSignal(int, int)        # sent, failed
    error    = pyqtSignal(str)             # fatal error message

    def __init__(self, vendors, subject, html_body, attachments,
                 smtp_host, smtp_port, email, password, sender_name,
                 parent=None):
        super().__init__(parent)
        self.vendors     = vendors
        self.subject     = subject
        self.html_body   = html_body
        self.attachments = attachments
        self.smtp_host   = smtp_host
        self.smtp_port   = smtp_port
        self.email       = email
        self.password    = password
        self.sender_name = sender_name
        self._stop       = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.email, self.password)
        except smtplib.SMTPAuthenticationError:
            self.error.emit(
                "Login failed — wrong email or password.\n\n"
                "If you use Microsoft 365, generate an App Password:\n"
                "  mysignins.microsoft.com → Security → App passwords"
            )
            return
        except Exception as e:
            self.error.emit(
                f"Could not connect to {self.smtp_host}:{self.smtp_port}\n\n"
                f"Check your internet connection and SMTP settings.\n\nDetail: {e}"
            )
            return

        sent = failed = 0

        for i, vendor in enumerate(self.vendors):
            if self._stop:
                break
            try:
                msg = self._build_message(vendor["name"], vendor["email"])
                server.send_message(msg)
                sent += 1
                self.progress.emit(i, "Sent", "")
            except Exception as e:
                failed += 1
                self.progress.emit(i, "Failed", str(e))

        try:
            server.quit()
        except Exception:
            pass

        self.finished.emit(sent, failed)

    def _build_message(self, vendor_name: str, vendor_email: str):
        subject = self.subject.replace("{{Name}}", vendor_name)
        html    = self.html_body.replace("{{Name}}", vendor_name)
        html, images = _extract_inline_images(html)

        msg = MIMEMultipart("mixed")
        msg["From"]    = f"{self.sender_name} <{self.email}>"
        msg["To"]      = vendor_email
        msg["Subject"] = subject

        # HTML + inline images go inside a "related" container
        related = MIMEMultipart("related")
        related.attach(MIMEText(html, "html", "utf-8"))

        for cid, img_data, img_type in images:
            img_part = MIMEImage(img_data, _subtype=img_type)
            img_part.add_header("Content-ID", f"<{cid}>")
            img_part.add_header("Content-Disposition", "inline")
            related.attach(img_part)

        msg.attach(related)

        # PDF attachments
        for path in self.attachments:
            if os.path.isfile(path):
                with open(path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{os.path.basename(path)}"'
                )
                msg.attach(part)

        return msg


def _extract_inline_images(html: str) -> tuple[str, list]:
    """Replace base64 data URIs with cid: references, return image bytes list."""
    images  = []
    counter = [0]

    def replace(match):
        data_uri = match.group(1)
        m = re.match(r"data:image/(\w+);base64,(.+)", data_uri, re.DOTALL)
        if not m:
            return match.group(0)
        img_type = m.group(1)
        img_data = base64.b64decode(m.group(2))
        counter[0] += 1
        cid = f"img{counter[0]}@massmail"
        images.append((cid, img_data, img_type))
        return f'src="cid:{cid}"'

    modified = re.sub(r'src="(data:image/[^"]+)"', replace, html, flags=re.DOTALL)
    return modified, images
