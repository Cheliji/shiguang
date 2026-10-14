"""DateBar 周日期栏组件（规格：UI 设计文档 §4.1.3 / §5.2）。

白色卡片容器 + 左右翻周箭头 + 7 个日期项（周一为一周开始）。
选中态主色填充；有待办的日期底部 4px 圆点。
"""

from datetime import date, timedelta

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QToolButton, QVBoxLayout, QWidget

from shiguang.ui.icons import colored_icon
from shiguang.ui.theme import Color, FontSize, Space

WEEKDAY_LABELS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def week_dates(anchor: date) -> list[date]:
    """返回 anchor 所在周的 7 天（周一开始）。纯函数。"""
    monday = anchor - timedelta(days=anchor.weekday())
    return [monday + timedelta(days=i) for i in range(7)]


_DAY_QSS = f"""
DayItem {{
    background: transparent;
    border-radius: 8px;
}}
DayItem:hover {{
    background: {Color.BG_SECONDARY};
}}
DayItem[selected="true"] {{
    background: {Color.PRIMARY};
}}
"""


class DayItem(QFrame):
    """单个日期项：星期文字 + 日期数字 + 待办圆点。"""

    clicked = Signal(date)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dayItem")
        self.setProperty("selected", False)
        self.setStyleSheet(_DAY_QSS)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._date: date | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Space.MD, Space.SM, Space.MD, Space.SM)
        layout.setSpacing(2)

        self.weekday_label = QLabel(self)
        self.weekday_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.weekday_label.setStyleSheet(f"font-size: {FontSize.TINY}px;")
        layout.addWidget(self.weekday_label)

        self.day_label = QLabel(self)
        self.day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.day_label.setStyleSheet(f"font-size: {FontSize.BODY}px;")
        layout.addWidget(self.day_label)

        self.dot = QLabel(self)
        self.dot.setFixedSize(4, 4)
        self.dot.hide()
        dot_row = QHBoxLayout()
        dot_row.setContentsMargins(0, 0, 0, 0)
        dot_row.addStretch(1)
        dot_row.addWidget(self.dot)
        dot_row.addStretch(1)
        layout.addLayout(dot_row)

        self._refresh_style()

    def set_data(self, day: date, has_todos: bool) -> None:
        self._date = day
        self.weekday_label.setText(WEEKDAY_LABELS[day.weekday()])
        self.day_label.setText(str(day.day))
        self.has_todos = has_todos
        self._refresh_style()

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)
        self._refresh_style()

    def is_selected(self) -> bool:
        return self.property("selected") is True or self.property("selected") == "true"

    def _refresh_style(self) -> None:
        selected = self.property("selected") in (True, "true")
        text_color = "#FFFFFF" if selected else Color.TEXT_PRIMARY
        weekday_color = "#FFFFFF" if selected else Color.TEXT_SECONDARY
        self.weekday_label.setStyleSheet(f"font-size: {FontSize.TINY}px; color: {weekday_color};")
        self.day_label.setStyleSheet(f"font-size: {FontSize.BODY}px; color: {text_color};")
        if getattr(self, "has_todos", False):
            dot_color = "#FFFFFF" if selected else Color.PRIMARY
            self.dot.setStyleSheet(f"background: {dot_color}; border-radius: 2px;")
            self.dot.show()
        else:
            self.dot.hide()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._date is not None:
            self.clicked.emit(self._date)

    def sizeHint(self) -> QSize:
        return QSize(64, 56)


class DateBar(QFrame):
    """周日期栏。"""

    date_selected = Signal(date)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dateBar")
        self.setStyleSheet(f"DateBar {{ background: {Color.SURFACE}; border-radius: 12px; }}")

        self._anchor = date.today()
        self._selected: date = date.today()
        self._todo_dates: set[date] = set()
        self._items: list[DayItem] = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(Space.LG, Space.MD, Space.LG, Space.MD)
        layout.setSpacing(Space.XS)

        self.prev_button = self._arrow("chevron-left", -7)
        self.next_button = self._arrow("chevron-right", 7)
        layout.addWidget(self.prev_button)

        for _ in range(7):
            item = DayItem(self)
            item.clicked.connect(self._on_day_clicked)
            layout.addWidget(item, 1)
            self._items.append(item)

        layout.addWidget(self.next_button)

        self.refresh()

    def _arrow(self, icon: str, days: int) -> QToolButton:
        button = QToolButton(self)
        button.setIcon(colored_icon(icon, Color.TEXT_SECONDARY, 16))
        button.setFixedSize(24, 24)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setStyleSheet(
            "QToolButton { border: none; border-radius: 12px; }"
            f"QToolButton:hover {{ background: {Color.BG_SECONDARY}; }}"
        )
        button.clicked.connect(lambda: self.shift_week(days))
        return button

    # ---------- 公共接口 ----------
    def set_week(self, anchor: date) -> None:
        """把日期栏定位到 anchor 所在的周。"""
        self._anchor = anchor
        self.refresh()

    def set_todo_dates(self, dates: set[date]) -> None:
        """设置有待办的日期（控制圆点）。"""
        self._todo_dates = set(dates)
        self.refresh()

    def set_selected(self, day: date) -> None:
        self._selected = day
        self.refresh()

    def shift_week(self, days: int) -> None:
        self._anchor += timedelta(days=days)
        self.refresh()

    def selected_date(self) -> date:
        return self._selected

    def refresh(self) -> None:
        days = week_dates(self._anchor)
        for item, day in zip(self._items, days, strict=True):
            item.set_data(day, day in self._todo_dates)
            item.set_selected(day == self._selected)

    def _on_day_clicked(self, day: date) -> None:
        self._selected = day
        self.refresh()
        self.date_selected.emit(day)
