"""页面占位基类。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from shiguang.ui.theme import Color, FontSize


class PlaceholderPage(QWidget):
    """占位页：居中显示提示文案。"""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(text, self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f"color: {Color.TEXT_TERTIARY}; font-size: {FontSize.BODY}px;")
        layout.addWidget(label)
