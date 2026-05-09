import base64
import os
import re
import tempfile

from PyQt6.QtCore import QThread, pyqtSignal


class EmailSenderThread(QThread):
    """
    Sends emails one by one via Outlook COM in a background thread.
    Emits progress and result signals so the UI can update live.
    """
    progress = pyqtSignal(int, str, str)   # index, status ("Sent"/"Failed"), detail
    finished = pyqtSignal(int, int)        # sent_count, failed_count
    error = pyqtSignal(str)               # fatal error (Outlook not found etc.)

    def __init__(self, vendors, subject, html_body, attachments, parent=None):
        super().__init__(parent)
        self.vendors = vendors
        self.subject = subject
        self.html_body = html_body
        self.attachments = attachments  # list of absolute file paths
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        # Import here so the module loads on Windows only at send time
        try:
            import pythoncom
            import win32com.client
        except ImportError:
            self.error.emit(
                "pywin32 is not installed.\n"
                "Run:  pip install pywin32"
            )
            return

        pythoncom.CoInitialize()
        try:
            outlook = win32com.client.Dispatch("Outlook.Application")
        except Exception as e:
            self.error.emit(
                f"Could not connect to Outlook.\n"
                f"Make sure Outlook is installed and open.\n\nDetail: {e}"
            )
            pythoncom.CoUninitialize()
            return

        sent = 0
        failed = 0

        for i, vendor in enumerate(self.vendors):
            if self._stop:
                break

            name = vendor["name"]
            email = vendor["email"]
            subject = self.subject.replace("{{Name}}", name)
            html, temp_images = _process_inline_images(self.html_body)
            html = html.replace("{{Name}}", name)

            try:
                mail = outlook.CreateItem(0)  # olMailItem
                mail.To = email
                mail.Subject = subject
                mail.HTMLBody = html

                # Attach inline images with Content-ID so they show in body
                for cid, path in temp_images:
                    att = mail.Attachments.Add(path)
                    att.PropertyAccessor.SetProperty(
                        "http://schemas.microsoft.com/mapi/proptag/0x3712001E", cid
                    )

                # Attach PDFs
                for pdf_path in self.attachments:
                    if os.path.isfile(pdf_path):
                        mail.Attachments.Add(pdf_path)

                mail.Send()
                sent += 1
                self.progress.emit(i, "Sent", "")
            except Exception as e:
                failed += 1
                self.progress.emit(i, "Failed", str(e))
            finally:
                for _, path in temp_images:
                    try:
                        os.unlink(path)
                    except OSError:
                        pass

        pythoncom.CoUninitialize()
        self.finished.emit(sent, failed)


def _process_inline_images(html_body: str) -> tuple[str, list[tuple[str, str]]]:
    """
    Finds base64 data URIs in <img src="..."> tags, saves each to a temp file,
    returns modified HTML (with cid: references) and list of (cid, filepath).
    """
    temp_images: list[tuple[str, str]] = []
    counter = [0]

    def replace(match):
        data_uri = match.group(1)
        m = re.match(r"data:image/(\w+);base64,(.+)", data_uri, re.DOTALL)
        if not m:
            return match.group(0)
        ext = m.group(1)
        raw = base64.b64decode(m.group(2))
        counter[0] += 1
        cid = f"img{counter[0]}@massmail"
        tmp = tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False)
        tmp.write(raw)
        tmp.close()
        temp_images.append((cid, tmp.name))
        return f'src="cid:{cid}"'

    modified = re.sub(r'src="(data:image/[^"]+)"', replace, html_body, flags=re.DOTALL)
    return modified, temp_images
