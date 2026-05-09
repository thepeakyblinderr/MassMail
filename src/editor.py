import base64

from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QAction, QColor, QFont, QIcon, QImage, QKeySequence,
    QTextCharFormat, QTextCursor, QTextListFormat,
)
from PyQt6.QtWidgets import (
    QColorDialog, QComboBox, QFileDialog, QFontComboBox,
    QHBoxLayout, QTextEdit, QToolBar, QToolButton, QVBoxLayout, QWidget,
)


class RichTextEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.toolbar = self._build_toolbar()
        layout.addWidget(self.toolbar)

        self.editor = QTextEdit()
        self.editor.setMinimumHeight(260)
        self.editor.setAcceptRichText(True)
        self.editor.setPlaceholderText(
            "Compose your email here…\n\nTip: Use {{Name}} where you want each vendor's name inserted automatically."
        )
        self.editor.setStyleSheet("""
            QTextEdit {
                background: #ffffff;
                border: 1px solid #d1d5db;
                border-top: none;
                border-radius: 0 0 6px 6px;
                padding: 12px;
                font-size: 13px;
                color: #1f2937;
            }
        """)
        self.editor.currentCharFormatChanged.connect(self._update_toolbar_state)
        layout.addWidget(self.editor)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def toHtml(self) -> str:
        return self.editor.toHtml()

    def setHtml(self, html: str):
        self.editor.setHtml(html)

    def clear(self):
        self.editor.clear()

    # ------------------------------------------------------------------
    # Toolbar construction
    # ------------------------------------------------------------------

    def _build_toolbar(self) -> QToolBar:
        tb = QToolBar()
        tb.setMovable(False)
        tb.setStyleSheet("""
            QToolBar {
                background: #f3f4f6;
                border: 1px solid #d1d5db;
                border-radius: 6px 6px 0 0;
                padding: 4px 6px;
                spacing: 2px;
            }
            QToolButton {
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 3px 6px;
                font-size: 13px;
                color: #374151;
            }
            QToolButton:hover { background: #e5e7eb; border-color: #d1d5db; }
            QToolButton:checked { background: #dbeafe; border-color: #93c5fd; color: #1d4ed8; }
            QComboBox {
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 2px 6px;
                background: #ffffff;
                font-size: 12px;
                min-width: 48px;
            }
            QFontComboBox {
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 2px 4px;
                background: #ffffff;
                font-size: 12px;
                min-width: 120px;
            }
        """)

        # Font family
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont("Calibri"))
        self.font_combo.currentFontChanged.connect(self._set_font_family)
        tb.addWidget(self.font_combo)

        # Font size
        self.size_combo = QComboBox()
        for s in ["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "32", "36", "48", "72"]:
            self.size_combo.addItem(s)
        self.size_combo.setCurrentText("12")
        self.size_combo.currentTextChanged.connect(self._set_font_size)
        tb.addWidget(self.size_combo)

        tb.addSeparator()

        # Bold
        self.act_bold = QAction("B", tb)
        self.act_bold.setCheckable(True)
        self.act_bold.setShortcut(QKeySequence.StandardKey.Bold)
        self.act_bold.triggered.connect(self._toggle_bold)
        btn_bold = tb.addAction(self.act_bold)
        tb.widgetForAction(self.act_bold).setFont(QFont("Arial", 11, QFont.Weight.Bold))

        # Italic
        self.act_italic = QAction("I", tb)
        self.act_italic.setCheckable(True)
        self.act_italic.setShortcut(QKeySequence.StandardKey.Italic)
        self.act_italic.triggered.connect(self._toggle_italic)
        tb.addAction(self.act_italic)
        tb.widgetForAction(self.act_italic).setFont(QFont("Arial", 11, QFont.Weight.Normal, True))

        # Underline
        self.act_underline = QAction("U", tb)
        self.act_underline.setCheckable(True)
        self.act_underline.setShortcut(QKeySequence.StandardKey.Underline)
        self.act_underline.triggered.connect(self._toggle_underline)
        tb.addAction(self.act_underline)

        tb.addSeparator()

        # Text colour
        self.color_btn = QToolButton()
        self.color_btn.setText("A▾")
        self.color_btn.setToolTip("Text colour")
        self._text_color = QColor("#000000")
        self.color_btn.clicked.connect(self._pick_text_color)
        tb.addWidget(self.color_btn)

        # Highlight colour
        self.highlight_btn = QToolButton()
        self.highlight_btn.setText("H▾")
        self.highlight_btn.setToolTip("Highlight colour")
        self.highlight_btn.clicked.connect(self._pick_highlight_color)
        tb.addWidget(self.highlight_btn)

        tb.addSeparator()

        # Alignment
        self.act_left = QAction("⬛L", tb)
        self.act_left.setCheckable(True)
        self.act_left.setToolTip("Align left")
        self.act_left.triggered.connect(lambda: self._set_alignment(Qt.AlignmentFlag.AlignLeft))

        self.act_center = QAction("▥C", tb)
        self.act_center.setCheckable(True)
        self.act_center.setToolTip("Align centre")
        self.act_center.triggered.connect(lambda: self._set_alignment(Qt.AlignmentFlag.AlignHCenter))

        self.act_right = QAction("⬛R", tb)
        self.act_right.setCheckable(True)
        self.act_right.setToolTip("Align right")
        self.act_right.triggered.connect(lambda: self._set_alignment(Qt.AlignmentFlag.AlignRight))

        for act in (self.act_left, self.act_center, self.act_right):
            tb.addAction(act)
        self.act_left.setChecked(True)

        tb.addSeparator()

        # Bullet list
        act_bullet = QAction("• List", tb)
        act_bullet.setToolTip("Bullet list")
        act_bullet.triggered.connect(self._insert_bullet_list)
        tb.addAction(act_bullet)

        # Numbered list
        act_numbered = QAction("1. List", tb)
        act_numbered.setToolTip("Numbered list")
        act_numbered.triggered.connect(self._insert_numbered_list)
        tb.addAction(act_numbered)

        tb.addSeparator()

        # Insert image
        act_img = QAction("🖼 Image", tb)
        act_img.setToolTip("Insert image into email body")
        act_img.triggered.connect(self._insert_image)
        tb.addAction(act_img)

        return tb

    # ------------------------------------------------------------------
    # Formatting actions
    # ------------------------------------------------------------------

    def _set_font_family(self, font: QFont):
        fmt = QTextCharFormat()
        fmt.setFontFamilies([font.family()])
        self._merge_format(fmt)

    def _set_font_size(self, size_str: str):
        try:
            size = int(size_str)
        except ValueError:
            return
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        self._merge_format(fmt)

    def _toggle_bold(self, checked: bool):
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold if checked else QFont.Weight.Normal)
        self._merge_format(fmt)

    def _toggle_italic(self, checked: bool):
        fmt = QTextCharFormat()
        fmt.setFontItalic(checked)
        self._merge_format(fmt)

    def _toggle_underline(self, checked: bool):
        fmt = QTextCharFormat()
        fmt.setFontUnderline(checked)
        self._merge_format(fmt)

    def _pick_text_color(self):
        color = QColorDialog.getColor(self._text_color, self, "Text Colour")
        if color.isValid():
            self._text_color = color
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            self._merge_format(fmt)
            self.color_btn.setStyleSheet(f"color: {color.name()};")

    def _pick_highlight_color(self):
        color = QColorDialog.getColor(QColor("#ffff00"), self, "Highlight Colour")
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setBackground(color)
            self._merge_format(fmt)

    def _set_alignment(self, alignment):
        self.editor.setAlignment(alignment)
        self.act_left.setChecked(alignment == Qt.AlignmentFlag.AlignLeft)
        self.act_center.setChecked(alignment == Qt.AlignmentFlag.AlignHCenter)
        self.act_right.setChecked(alignment == Qt.AlignmentFlag.AlignRight)

    def _insert_bullet_list(self):
        cursor = self.editor.textCursor()
        fmt = QTextListFormat()
        fmt.setStyle(QTextListFormat.Style.ListDisc)
        cursor.createList(fmt)

    def _insert_numbered_list(self):
        cursor = self.editor.textCursor()
        fmt = QTextListFormat()
        fmt.setStyle(QTextListFormat.Style.ListDecimal)
        cursor.createList(fmt)

    def _insert_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Insert Image", "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp)"
        )
        if not path:
            return
        with open(path, "rb") as f:
            data = f.read()
        ext = path.rsplit(".", 1)[-1].lower()
        b64 = base64.b64encode(data).decode()
        data_uri = f"data:image/{ext};base64,{b64}"

        cursor = self.editor.textCursor()
        img = QImage(path)
        # Scale down if very large for display
        if img.width() > 600:
            img = img.scaledToWidth(600, Qt.TransformationMode.SmoothTransformation)
        cursor.insertImage(img, data_uri)  # stores as resource keyed by data_uri

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _merge_format(self, fmt: QTextCharFormat):
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.mergeCharFormat(fmt)
        self.editor.mergeCurrentCharFormat(fmt)

    def _update_toolbar_state(self, fmt: QTextCharFormat):
        self.act_bold.setChecked(fmt.fontWeight() == QFont.Weight.Bold)
        self.act_italic.setChecked(fmt.fontItalic())
        self.act_underline.setChecked(fmt.fontUnderline())
        if fmt.fontPointSize() > 0:
            self.size_combo.setCurrentText(str(int(fmt.fontPointSize())))
        families = fmt.fontFamilies()
        if families:
            self.font_combo.setCurrentFont(QFont(families[0]))
