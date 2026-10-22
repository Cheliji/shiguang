"""日期选择按钮 + 自绘日历弹窗（替代 Qt 原生 QCalendarWidget）。

渲染策略（关键）：
- 整个日历（圆角卡片、主题色头部、星期表头、日期数字、选中高亮、悬停反馈）
  全部由 CalendarPopup.paintEvent 一次 QPainter 绘制，日期格仅保留透明命中区按钮。
  不使用子控件 QSS 背景、不使用 QGraphicsDropShadowEffect —— 这两者在
  WA_TranslucentBackground 的 Popup 窗口下会缓存渲染结果，刷新后易残留旧像素。
  任何状态变化都整体 update()，逐帧全量重绘，杜绝残留。

交互规则（对齐用户需求）：
- 头部背景为主题色 PRIMARY，左右上角仅 < > 矢量按钮按月步进，年份随跨年自动变化；
- 年/月只读，不可输入；禁止鼠标滚轮操作；
- 当月日期白色背景、非当月日期灰色；
- 默认选中当日并以主题色实心圆凸显；选中其他日期后当日立即恢复纯白，
  全弹窗始终只有「选中日期」一个高亮，且与进入时的当日高亮样式完全一致。

窗口层面（避免「圆角外一圈直角边框」）：
- 无边框 + WA_TranslucentBackground 透明窗口，且用圆角 QRegion 做窗口 mask，
  窗口物理上只有圆角形状，圆角以外不存在任何像素（不会出现直角边框）；
- 不画窗口投影：投影是沿窗口矩形的直角阴影，会形成一圈方形边框感；
- 显式加 Qt.NoDropShadowWindowHint：Windows 会给 Popup 类窗口加
  CS_DROPSHADOW，同样是直角系统阴影，必须禁用；
- 弹窗自身样式强制 background: transparent，避免全局 QSS 填出直角底色。
"""

from PySide6.QtCore import QDate, QEvent, QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QRegion
from PySide6.QtWidgets import QApplication, QPushButton, QToolButton, QWidget
from shiboken6 import isValid

from shiguang.ui.icons import colored_icon
from shiguang.ui.theme import Color, FontSize, Radius, Space

_TRIGGER_QSS = f"""
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

# 命中区按钮：完全透明，只负责点击与悬停事件，视觉全部由弹窗自绘
_HIT_QSS = "background: transparent; border: none;"

# 弹窗自身背景强制透明：避免全局样式表（QStyleSheetStyle）给顶层窗口填出直角底色
_POPUP_QSS = "CalendarPopup { background: transparent; border: none; }"

# 布局常量（周一起始，与代办表单 WEEKDAY_NAMES 约定一致）
_WEEKDAY_HEADERS = ["一", "二", "三", "四", "五", "六", "日"]
_CELL = 36
_GAP = 4
_PAD = 12
_HEADER_HEIGHT = 48
_WEEKDAY_HEIGHT = 22

_CARD_WIDTH = _PAD * 2 + 7 * _CELL + 6 * _GAP
_CARD_HEIGHT = _HEADER_HEIGHT + 8 + _WEEKDAY_HEIGHT + 8 + 6 * _CELL + 5 * _GAP + _PAD
_GRID_TOP = _HEADER_HEIGHT + 8 + _WEEKDAY_HEIGHT + 8
_WEEKDAY_TOP = _HEADER_HEIGHT + 8


class CalendarPopup(QWidget):
    """自绘日历弹窗：一次 QPainter 全量绘制，仅供 DatePickerButton 使用。"""

    dateSelected = Signal(QDate)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # 顶层独立窗口：不继承对话框（qfluentwidgets MessageBoxBase）的样式表，
        # 避免外部 QSS（如 QLabel{color:black}）干扰日历配色。
        # NoDropShadowWindowHint：Windows 会给 Popup 窗口加 CS_DROPSHADOW，
        # 那是【直角矩形】系统投影，会围着圆角卡片露出一圈方形边框，必须关掉。
        self.setWindowFlags(
            Qt.WindowType.Popup
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAutoFillBackground(False)
        self.setStyleSheet(_POPUP_QSS)
        # 窗口尺寸 = 卡片尺寸：不留任何矩形留白，避免圆角外出现直角区域
        self.setFixedSize(_CARD_WIDTH, _CARD_HEIGHT)
        # 圆角窗口形状：用 mask 把窗口物理裁剪成圆角矩形，
        # 即使系统/样式表在窗口矩形上绘制任何东西，圆角外也不会存在像素
        self._apply_rounded_mask()
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._month = QDate(QDate.currentDate().year(), QDate.currentDate().month(), 1)
        self._selected: QDate = QDate.currentDate()
        self._hover: QDate | None = None
        self._dates: list[QDate] = []

        # 日期命中区（透明按钮，不绘制任何视觉）
        self._day_buttons: list[QPushButton] = []
        for _index in range(42):
            button = QPushButton(self)
            button.setStyleSheet(_HIT_QSS)
            button.setFlat(True)
            button.setFixedSize(_CELL, _CELL)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.installEventFilter(self)
            button.clicked.connect(lambda _c=False, b=button: self._on_day_clicked(b))
            self._day_buttons.append(button)

        self._prev_button = self._make_nav_button("chevron-left", "上个月", -1)
        self._next_button = self._make_nav_button("chevron-right", "下个月", 1)

        self._refresh()

    # ---------- 结构 ----------
    def _make_nav_button(self, icon_name: str, tip: str, step: int) -> QToolButton:
        button = QToolButton(self)
        button.setIcon(colored_icon(icon_name, "#FFFFFF", 18))
        button.setFixedSize(32, 32)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setToolTip(tip)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setStyleSheet(
            "QToolButton { background: transparent; border: none; border-radius: 6px; }"
            "QToolButton:hover { background: rgba(255, 255, 255, 0.18); }"
            "QToolButton:pressed { background: rgba(255, 255, 255, 0.30); }"
        )
        button.clicked.connect(lambda _c=False: self._navigate(step))
        return button

    # ---------- 状态 ----------
    def reset(self, initial: QDate | None = None) -> None:
        """打开弹窗时初始化：默认选中当日（凸显）；有预设日期则选中预设日期。"""
        self._selected = QDate(initial) if initial is not None else QDate.currentDate()
        self._month = QDate(self._selected.year(), self._selected.month(), 1)
        self._hover = None
        self._refresh()

    def _navigate(self, step: int) -> None:
        """按月步进切换，年份随跨月/跨年自动变化。"""
        self._month = self._month.addMonths(step)
        self._refresh()

    def _refresh(self) -> None:
        # 周一起始：dayOfWeek() 周一=1 … 周日=7 → 列索引 = dayOfWeek()-1
        start = self._month.addDays(-(self._month.dayOfWeek() - 1))
        self._dates = [start.addDays(i) for i in range(42)]
        for button, day in zip(self._day_buttons, self._dates, strict=True):
            button._date = day  # noqa: SLF001 — 命中区内部数据载体
        self._layout_children()
        self.update()  # 整体重绘：不依赖增量刷新，旧高亮不可能残留

    def _layout_children(self) -> None:
        self._prev_button.move(_PAD - 4, 8)
        self._next_button.move(_CARD_WIDTH - _PAD - 28, 8)
        grid_x = _PAD
        grid_y = _GRID_TOP
        for index, button in enumerate(self._day_buttons):
            row, col = divmod(index, 7)
            button.move(grid_x + col * (_CELL + _GAP), grid_y + row * (_CELL + _GAP))

    def title_text(self) -> str:
        return f"{self._month.year()}年 {self._month.month()}月"

    # ---------- 绘制 ----------
    def _card_path(self, card: QRectF) -> QPainterPath:
        path = QPainterPath()
        path.addRoundedRect(card, Radius.LG, Radius.LG)
        return path

    def _apply_rounded_mask(self) -> None:
        """把窗口裁剪成圆角矩形：圆角外不留任何像素，从物理上消除直角边框。"""
        card = QRectF(0, 0, self.width(), self.height())
        self.setMask(QRegion(self._card_path(card).toFillPolygon().toPolygon()))

    def resizeEvent(self, event) -> None:  # noqa: N802 — Qt 命名
        """尺寸/DPI 变化时重算圆角 mask。"""
        super().resizeEvent(event)
        self._apply_rounded_mask()

    def paintEvent(self, event) -> None:  # noqa: N802 — Qt 命名
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        card = QRectF(0, 0, _CARD_WIDTH, _CARD_HEIGHT)

        self._paint_card(painter, card)

        painter.save()
        painter.setClipPath(self._card_path(card))
        self._paint_header(painter, card)
        self._paint_weekdays(painter, card)
        self._paint_days(painter)
        painter.restore()

    @staticmethod
    def _paint_card(painter: QPainter, card: QRectF) -> None:
        """白色圆角卡片 + 1px 描边（手绘保证圆角无直角残留）。"""
        painter.setPen(QPen(QColor(Color.BG_SECONDARY), 1))
        painter.setBrush(QColor(Color.SURFACE))
        painter.drawRoundedRect(card.adjusted(0.5, 0.5, -0.5, -0.5), Radius.LG, Radius.LG)

    def _paint_header(self, painter: QPainter, card: QRectF) -> None:
        """主题色头部（仅顶部圆角）：年月文本只读居中，左右为 < > 按钮。"""
        header = QRectF(card.left(), card.top(), card.width(), _HEADER_HEIGHT)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(Color.PRIMARY))
        painter.drawRoundedRect(header, Radius.LG, Radius.LG)
        painter.drawRect(
            QRectF(
                header.left(),
                header.top() + Radius.LG,
                header.width(),
                _HEADER_HEIGHT - Radius.LG,
            )
        )

        font = QFont(self.font())
        font.setPixelSize(FontSize.CARD_TITLE)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(header, Qt.AlignmentFlag.AlignCenter, self.title_text())

    def _paint_weekdays(self, painter: QPainter, card: QRectF) -> None:
        font = QFont(self.font())
        font.setPixelSize(FontSize.TINY)
        painter.setFont(font)
        painter.setPen(QColor(Color.TEXT_SECONDARY))
        top = card.top() + _WEEKDAY_TOP
        for col, name in enumerate(_WEEKDAY_HEADERS):
            cell = QRectF(card.left() + _PAD + col * (_CELL + _GAP), top, _CELL, _WEEKDAY_HEIGHT)
            painter.drawText(cell, Qt.AlignmentFlag.AlignCenter, name)

    def _paint_days(self, painter: QPainter) -> None:
        """日期数字与高亮：唯一高亮 = 选中日期（主题色实心圆 + 白字）。"""
        normal_font = QFont(self.font())
        normal_font.setPixelSize(FontSize.AUXILIARY)
        bold_font = QFont(normal_font)
        bold_font.setBold(True)

        for button, day in zip(self._day_buttons, self._dates, strict=True):
            cell = QRectF(button.geometry())
            active = day == self._selected
            outside = day.month() != self._month.month()

            if active:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(Color.PRIMARY))
                painter.drawEllipse(cell.adjusted(0.5, 0.5, -0.5, -0.5))
                color = QColor("#FFFFFF")
                painter.setFont(bold_font)
            elif outside:
                color = QColor(Color.TEXT_TERTIARY)
                painter.setFont(normal_font)
            else:
                if self._hover == day:
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QColor(Color.PRIMARY_LIGHT))
                    painter.drawEllipse(cell.adjusted(0.5, 0.5, -0.5, -0.5))
                    color = QColor(Color.PRIMARY)
                else:
                    color = QColor(Color.TEXT_PRIMARY)
                painter.setFont(normal_font)

            painter.setPen(color)
            painter.drawText(cell, Qt.AlignmentFlag.AlignCenter, str(day.day()))

    # ---------- 交互 ----------
    def eventFilter(self, obj, event) -> bool:  # noqa: N802 — Qt 命名
        """日期格悬停反馈：进入/离开时更新悬停日期并整体重绘。"""
        # 窗口销毁过程中 C++ 对象可能已被销毁，此时直接放行
        if not isValid(self):
            return False
        if isinstance(obj, QPushButton) and getattr(obj, "_date", None) is not None:
            if event.type() == QEvent.Type.Enter:
                self._hover = obj._date  # noqa: SLF001
                self.update()
            elif event.type() == QEvent.Type.Leave:
                if self._hover == obj._date:  # noqa: SLF001
                    self._hover = None
                    self.update()
        return super().eventFilter(obj, event)

    def _on_day_clicked(self, button: QPushButton) -> None:
        day = getattr(button, "_date", None)
        if day is None:
            return
        self._selected = QDate(day)
        self._refresh()  # 先刷新：选中其他日期后，原高亮（含当日）立即恢复纯白
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
        self.setStyleSheet(_TRIGGER_QSS)
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
        if self._popup is None or not isValid(self._popup):
            self._popup = CalendarPopup()  # 顶层独立窗口：不继承对话框样式表
            self._popup.destroyed.connect(self._on_popup_destroyed)
            self._popup.dateSelected.connect(self._on_date_selected)
            app = QApplication.instance()
            if app is not None:
                app.aboutToQuit.connect(self._on_app_about_to_quit)
        # 无预设日期时默认选中当日（主题色凸显）
        self._popup.reset(self._date)
        self._popup.move(self.mapToGlobal(QPoint(0, self.height() + Space.XS)))
        self._popup.show()
        self._popup.raise_()
        self._popup.activateWindow()

    def _on_app_about_to_quit(self) -> None:
        if self._popup is not None and isValid(self._popup):
            self._popup.close()

    def _on_popup_destroyed(self) -> None:
        """弹窗 C++ 对象销毁后清除 Python 引用，避免后续调用崩溃。"""
        self._popup = None

    def hideEvent(self, event) -> None:  # noqa: N802 — Qt 命名
        """宿主对话框关闭/隐藏时一并收起日历弹窗，避免残留无主窗口。"""
        if self._popup is not None and isValid(self._popup):
            self._popup.close()
        super().hideEvent(event)

    def _on_date_selected(self, value: QDate) -> None:
        self._date = QDate(value)
        self._refresh_text()
        self.dateChanged.emit(self._date)
