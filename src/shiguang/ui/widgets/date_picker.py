"""日期选择按钮（替代 qfluentwidgets.CalendarPicker）。

触发器使用 Feather `calendar` 矢量图标 + 日期文本，点击后弹出系统日历控件选择日期，
避免 qfluentwidgets CalendarPicker 在对话框内点击无响应的兼容问题。
"""

from PySide6.QtCore import QDate, QPoint, Qt, Signal
from PySide6.QtWidgets import QCalendarWidget, QToolButton, QWidget

from shiguang.ui.icons import colored_icon
from shiguang.ui.theme import Color, FontSize

_BUTTON_QSS = f"""
QToolButton {{
    background: {Color.SURFACE};
    border: 1px solid {Color.BG_SECONDARY};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: {FontSize.BODY}px;
    color: {Color.TEXT_PRIMARY};
}}
QToolButton:hover {{
    border: 1px solid {Color.PRIMARY};
}}
QToolButton[placeholder="true"] {{
    color: {Color.TEXT_TERTIARY};
}}
"""


class DatePickerButton(QToolButton):
    """矢量日历按钮：点击弹出日历，选中后更新按钮文本并发出 dateChanged。

    支持可选模式（placeholder）：未设置日期时显示灰色占位文案，clearDate() 清空。
    """

    dateChanged = Signal(QDate)
    dateCleared = Signal()

    def __init__(self, parent: QWidget | None = None, placeholder: str = "选择日期") -> None:
        super().__init__(parent)
        self._date: QDate | None = None
        self._placeholder = placeholder
        self._popup: QCalendarWidget | None = None

        self.setIcon(colored_icon("calendar", Color.TEXT_SECONDARY, 16))
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(40)
        self.setStyleSheet(_BUTTON_QSS)
        self._refresh_text()
        self.clicked.connect(self._show_calendar)

    # ---------- 兼容 CalendarPicker 的常用 API ----------
    def getDate(self) -> QDate:
        """未设置日期时回退为今天（可选模式下请先用 hasDate() 判断）。"""
        return QDate(self._date) if self._date is not None else QDate.currentDate()

    def hasDate(self) -> bool:
        return self._date is not None

    def setDate(self, value: QDate) -> None:
        self._date = QDate(value)
        self._refresh_text()
        self.dateChanged.emit(self._date)

    def clearDate(self) -> None:
        if self._date is None:
            return
        self._date = None
        self._refresh_text()
        self.dateCleared.emit()

    # ---------- 交互 ----------
    def _refresh_text(self) -> None:
        if self._date is None:
            self.setText(self._placeholder)
            self.setProperty("placeholder", True)
        else:
            self.setText(self._date.toString(Qt.DateFormat.ISODate))
            self.setProperty("placeholder", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def _show_calendar(self) -> None:
        if self._popup is not None:
            self._popup.close()
            self._popup = None

        popup = QCalendarWidget(self.window())
        popup.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        popup.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        popup.setSelectedDate(self._date if self._date is not None else QDate.currentDate())
        popup.clicked.connect(self._on_date_clicked)
        popup.move(self.mapToGlobal(QPoint(0, self.height())))
        popup.show()
        self._popup = popup

    def _on_date_clicked(self, value: QDate) -> None:
        self._date = QDate(value)
        self._refresh_text()
        if self._popup is not None:
            self._popup.close()
            self._popup = None
        self.dateChanged.emit(self._date)
