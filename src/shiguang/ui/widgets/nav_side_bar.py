"""左侧图标导航栏（规格：UI 设计文档 §3.2.1）。

64px 固定宽、48px 图标按钮、选中竖线 + 浅主色背景、悬停态、500ms Tooltip。
设置项固定在底部，以分割线分隔。
"""

from PySide6.QtCore import QEvent, QObject, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QFrame, QHBoxLayout, QToolButton, QToolTip, QVBoxLayout, QWidget

from shiguang.ui.icons import colored_icon
from shiguang.ui.theme import Color, Layout

_NAV_QSS = f"""
NavSideBar {{
    background: {Color.SURFACE};
    border-right: 1px solid {Color.BG_SECONDARY};
}}
QToolButton {{
    border: none;
    border-radius: 8px;
    background: transparent;
}}
QToolButton:hover {{
    background: {Color.BG_PRIMARY};
}}
QToolButton:checked {{
    background: {Color.PRIMARY_LIGHT};
    border-left: 3px solid {Color.PRIMARY};
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
}}
"""


class _Divider(QFrame):
    """导航栏底部分割线。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(40, 1)
        self.setStyleSheet(f"background: {Color.BG_SECONDARY};")


class _DelayedTooltip(QObject):
    """500ms 悬停后显示 Tooltip（§3.2.1）。"""

    def __init__(self, button: QToolButton, text: str) -> None:
        super().__init__(button)
        self._button = button
        self._text = text
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._show)
        button.setToolTip("")  # 禁用 Qt 默认即时 Tooltip
        button.installEventFilter(self)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj is self._button:
            if event.type() == QEvent.Type.HoverEnter:
                self._timer.start()
            elif event.type() in (QEvent.Type.HoverLeave, QEvent.Type.Leave):
                self._timer.stop()
                QToolTip.hideText()
        return super().eventFilter(obj, event)

    def _show(self) -> None:
        QToolTip.showText(QCursor.pos(), self._text, self._button, QRect(), 3000)


class NavSideBar(QWidget):
    """图标导航栏。

    items: [(icon_name, tooltip)]，最后一项（设置）自动固定到底部。
    """

    page_selected = Signal(int)

    def __init__(self, items: list[tuple[str, str]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("navSideBar")
        self.setFixedWidth(Layout.NAV_WIDTH)
        self.setStyleSheet(_NAV_QSS)

        self._buttons: list[QToolButton] = []
        self._tooltips: list[_DelayedTooltip] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(4)

        for index, (icon_name, tooltip) in enumerate(items):
            if index == len(items) - 1:
                # 最后一项（设置）固定底部，上方加分隔线
                layout.addStretch(1)
                divider_row = QHBoxLayout()
                divider_row.addStretch(1)
                divider_row.addWidget(_Divider(self))
                divider_row.addStretch(1)
                layout.addLayout(divider_row)
                layout.addSpacing(4)

            button = QToolButton(self)
            button.setFixedSize(Layout.NAV_BUTTON, Layout.NAV_BUTTON)
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setProperty("icon_name", icon_name)
            button.clicked.connect(lambda checked=False, i=index: self.select(i))
            self._tooltips.append(_DelayedTooltip(button, tooltip))

            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.addStretch(1)
            row.addWidget(button)
            row.addStretch(1)
            layout.addLayout(row)

            self._buttons.append(button)

        self.select(0, emit=False)

    def button_count(self) -> int:
        return len(self._buttons)

    def select(self, index: int, emit: bool = True) -> None:
        """选中指定导航项，刷新图标着色与选中态。"""
        for i, button in enumerate(self._buttons):
            button.setChecked(i == index)
            color = Color.PRIMARY if i == index else Color.TEXT_SECONDARY
            button.setIcon(colored_icon(str(button.property("icon_name")), color))
        if emit:
            self.page_selected.emit(index)
