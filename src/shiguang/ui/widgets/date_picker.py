"""日期选择按钮 + 自绘日历弹窗（替代 Qt 原生 QCalendarWidget）。

设计要点（对齐用户需求）：
- 日历整体背景色与主题色一致：头部工具栏使用 PRIMARY（Teal）；
- 月份切换仅靠左右上角的 < > 矢量按钮（Feather chevron），步长 1 个月，
  年份随跨年自动变化，年/月不可输入；
- 禁止鼠标滚轮操作：忽略所有 wheel 事件；
- 当月日期背景为白色，非当月日期显示为灰色；
- 打开时默认定位到当月，今日用主题色圆形凸显。
"""

from PySide6.QtCore import QDate, QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from shiguang.ui.icons import colored_icon
from shiguang.ui.theme import Color, FontSize, Radius, Space

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

# 周一为一周之首（与代办表单 WEEKDAY_NAMES 约定一致）
_WEEKDAY_HEADERS = ["一", "二", "三", "四", "五", "六", "日"]
_CELL_SIZE = 36
_HEADER_HEIGHT = 48
_POPUP_QSS = f"""
#calTitle {{
    background: transparent;
    color: #FFFFFF;
    font-size: {FontSize.CARD_TITLE}px;
    font-weight: 600;
}}
QToolButton#calPrev, QToolButton#calNext {{
    background: transparent;
    border: none;
    border-radius: 6px;
}}
QToolButton#calPrev:hover, QToolButton#calNext:hover {{
    background: rgba(255, 255, 255, 0.18);
}}
QToolButton#calPrev:pressed, QToolButton#calNext:pressed {{
    background: rgba(255, 255, 255, 0.30);
}}
#calWeekday {{
    background: transparent;
    color: {Color.TEXT_SECONDARY};
    font-size: {FontSize.TINY}px;
}}
QPushButton[calDay="true"] {{
    background: {Color.SURFACE};
    color: {Color.TEXT_PRIMARY};
    border: none;
    border-radius: 16px;
    font-size: {FontSize.AUXILIARY}px;
}}
QPushButton[calDay="true"]:hover {{
    background: {Color.PRIMARY_LIGHT};
    color: {Color.PRIMARY};
}}
QPushButton[calDay="true"][outside="true"], QPushButton[calDay="true"][outside="true"]:hover {{
    background: {Color.SURFACE};
    color: {Color.TEXT_TERTIARY};
}}
QPushButton[calDay="true"][today="true"], QPushButton[calDay="true"][today="true"]:hover {{
    background: {Color.PRIMARY};
    color: #FFFFFF;
    font-weight: 600;
}}
QPushButton[calDay="true"][selected="true"] {{
    background: {Color.PRIMARY_LIGHT};
    color: {Color.PRIMARY};
    border: 1px solid {Color.PRIMARY};
    font-weight: 600;
}}
"""


class _CalendarCard(QFrame):
    """日历卡片：白色圆角底 + 主题色头部，用 QPainter 手绘。

    QSS 的 border-radius 在顶层弹窗边缘容易残留直角底色（窗口矩形背景
    未被裁剪），手绘抗锯齿圆角可彻底避免该问题。
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # 关闭 QFrame 默认绘制，背景完全由 paintEvent 接管
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def paintEvent(self, event) -> None:  # noqa: N802 — Qt 命名
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect())

        # 1) 白色圆角底 + 1px 描边（向内收缩 0.5px 避免描边被裁切）
        painter.setPen(QPen(QColor(Color.BG_SECONDARY), 1))
        painter.setBrush(QColor(Color.SURFACE))
        painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), Radius.LG, Radius.LG)

        # 2) 主题色头部：仅顶部两角圆角（先画全圆角矩形，再用矩形盖住底部圆角）
        header = QRectF(rect.left(), rect.top(), rect.width(), _HEADER_HEIGHT)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(Color.PRIMARY))
        painter.drawRoundedRect(header, Radius.LG, Radius.LG)
        painter.drawRect(QRectF(header.left(), header.top() + Radius.LG, header.width(), Radius.LG))


class CalendarPopup(QWidget):
    """自绘日历弹窗：主题色头部 + 白色日期网格，仅供 DatePickerButton 使用。"""

    dateSelected = Signal(QDate)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(_POPUP_QSS)

        self._month = QDate(QDate.currentDate().year(), QDate.currentDate().month(), 1)
        self._selected: QDate | None = None
        self._day_buttons: list[QPushButton] = []

        # 外层留白给投影，卡片手绘圆角 + 阴影彻底消除直角残留
        outer = QVBoxLayout(self)
        outer.setContentsMargins(Space.SM + 2, Space.SM, Space.SM + 2, Space.SM + 6)
        self._card = _CalendarCard(self)
        outer.addWidget(self._card)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 26))  # ≈ rgba(0,0,0,0.10)
        self._card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self._card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_header())

        # 星期表头 + 6×7 日期网格（固定 6 行，保证不同月份高度一致）
        grid = QGridLayout()
        grid.setContentsMargins(Space.SM, Space.SM, Space.SM, Space.SM)
        grid.setHorizontalSpacing(4)
        grid.setVerticalSpacing(4)
        for col, name in enumerate(_WEEKDAY_HEADERS):
            label = QLabel(name)
            label.setObjectName("calWeekday")
            label.setFixedSize(_CELL_SIZE, 20)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(label, 0, col)
        for index in range(42):
            row, col = divmod(index + 7, 7)
            button = QPushButton(self._card)
            button.setProperty("calDay", True)
            button.setFlat(True)
            button.setFixedSize(_CELL_SIZE, _CELL_SIZE)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.clicked.connect(lambda _c=False, b=button: self._on_day_clicked(b))
            self._day_buttons.append(button)
            grid.addWidget(button, row, col)
        layout.addLayout(grid)

    # ---------- 结构 ----------
    def _build_header(self) -> QFrame:
        """头部内容层（透明容器，主题色背景由 _CalendarCard 手绘）：
        左上 < 右上 > 矢量按钮，中间只读年月文本。"""
        header = QFrame(self._card)
        header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        header.setFixedHeight(_HEADER_HEIGHT)
        row = QHBoxLayout(header)
        row.setContentsMargins(Space.SM, Space.SM, Space.SM, Space.SM)
        row.setSpacing(0)

        self._prev_button = QToolButton(header)
        self._prev_button.setObjectName("calPrev")
        self._prev_button.setIcon(colored_icon("chevron-left", "#FFFFFF", 18))
        self._prev_button.setFixedSize(32, 32)
        self._prev_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._prev_button.setToolTip("上个月")
        self._prev_button.clicked.connect(lambda: self._navigate(-1))

        self._title_label = QLabel(header)
        self._title_label.setObjectName("calTitle")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._next_button = QToolButton(header)
        self._next_button.setObjectName("calNext")
        self._next_button.setIcon(colored_icon("chevron-right", "#FFFFFF", 18))
        self._next_button.setFixedSize(32, 32)
        self._next_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._next_button.setToolTip("下个月")
        self._next_button.clicked.connect(lambda: self._navigate(1))

        row.addWidget(self._prev_button)
        row.addWidget(self._title_label, 1)
        row.addWidget(self._next_button)
        return header

    # ---------- 状态 ----------
    def reset(self, initial: QDate | None = None) -> None:
        """打开弹窗时初始化：无预设日期则定位当月（今日凸显），否则定位预设日期所在月。"""
        today = QDate.currentDate()
        anchor = QDate(initial) if initial is not None else today
        self._selected = QDate(initial) if initial is not None else None
        self._month = QDate(anchor.year(), anchor.month(), 1)
        self._refresh()

    def _navigate(self, step: int) -> None:
        """按月步进切换，年份随跨月/跨年自动变化。"""
        self._month = self._month.addMonths(step)
        self._refresh()

    def _refresh(self) -> None:
        self._title_label.setText(f"{self._month.year()}年 {self._month.month()}月")
        today = QDate.currentDate()
        # 周一起始：dayOfWeek() 周一=1 … 周日=7 → 列索引 = dayOfWeek()-1
        lead = self._month.dayOfWeek() - 1
        start = self._month.addDays(-lead)
        for index, button in enumerate(self._day_buttons):
            day = start.addDays(index)
            is_today = day == today
            button.setText(str(day.day()))
            button.setProperty("outside", day.month() != self._month.month())
            button.setProperty("today", is_today)
            button.setProperty("selected", self._selected is not None and day == self._selected)
            button._date = day  # noqa: SLF001 — 弹窗内部数据载体
            button.style().unpolish(button)
            button.style().polish(button)

    # ---------- 交互 ----------
    def _on_day_clicked(self, button: QPushButton) -> None:
        day = getattr(button, "_date", None)
        if day is None:
            return
        self._selected = QDate(day)
        self.dateSelected.emit(self._selected)
        self.close()

    def wheelEvent(self, event) -> None:  # noqa: N802 — Qt 命名
        """禁止鼠标滚轮切换月份/日期。"""
        event.ignore()


class DatePickerButton(QToolButton):
    """矢量日历按钮：点击弹出主题色日历，选中后更新按钮文本并发出 dateChanged。

    支持可选模式（placeholder）：未设置日期时显示灰色占位文案，clearDate() 清空。
    """

    dateChanged = Signal(QDate)
    dateCleared = Signal()

    def __init__(self, parent: QWidget | None = None, placeholder: str = "选择日期") -> None:
        super().__init__(parent)
        self._date: QDate | None = None
        self._placeholder = placeholder
        self._popup: CalendarPopup | None = None

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
        if self._popup is None:
            self._popup = CalendarPopup(self.window())
            self._popup.dateSelected.connect(self._on_date_selected)
        # 无预设日期时默认定位当日（今日以主题色凸显）
        self._popup.reset(self._date)
        self._popup.move(self.mapToGlobal(QPoint(0, self.height() + Space.XS)))
        self._popup.show()
        self._popup.raise_()
        self._popup.activateWindow()

    def _on_date_selected(self, value: QDate) -> None:
        self._date = QDate(value)
        self._refresh_text()
        self.dateChanged.emit(self._date)
