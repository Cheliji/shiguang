"""主窗口（规格：UI 设计文档 §3）。

无边框窗口（禁止原生标题栏）+ 自绘标题栏 + 64px 图标导航 + 页面容器（淡入切换）。
"""

from PySide6.QtCore import QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect, QHBoxLayout, QStackedWidget, QWidget
from qframelesswindow import FramelessWindow

from shiguang.ui.pages import DiaryPage, SettingsPage, StatsPage, TodayPage, TodoPage
from shiguang.ui.theme import Color, Duration, Layout
from shiguang.ui.widgets.nav_side_bar import NavSideBar
from shiguang.ui.widgets.title_bar import AppTitleBar

NAV_ITEMS: list[tuple[str, str]] = [
    ("home", "今日"),
    ("check-square", "代办"),
    ("book-open", "日记"),
    ("bar-chart-2", "统计"),
    ("settings", "设置"),
]


class MainWindow(FramelessWindow):
    """拾光主窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("拾光")
        self.resize(Layout.WINDOW_WIDTH, Layout.WINDOW_HEIGHT)
        self.setMinimumSize(Layout.WINDOW_MIN_WIDTH, Layout.WINDOW_MIN_HEIGHT)
        self.setStyleSheet(f"MainWindow {{ background: {Color.BG_PRIMARY}; }}")

        # 自绘标题栏（FramelessWindow.setTitleBar 自带拖拽/双击最大化/边缘缩放支持）
        self.setTitleBar(AppTitleBar(self))
        self.titleBar.raise_()

        # 页面容器
        self.stack = QStackedWidget(self)
        self.pages: list[QWidget] = [
            TodayPage(self),
            TodoPage(self),
            DiaryPage(self),
            StatsPage(self),
            SettingsPage(self),
        ]
        for page in self.pages:
            self.stack.addWidget(page)

        # 导航
        self.nav = NavSideBar(NAV_ITEMS, self)
        self.nav.page_selected.connect(self.switch_page)

        # 布局：标题栏占据顶部（由 setTitleBar 管理），下方 导航 + 页面
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self.nav)
        body.addWidget(self.stack, 1)

        container = QWidget(self)
        container.setLayout(body)
        root = QHBoxLayout(self)
        root.setContentsMargins(0, Layout.TITLE_BAR_HEIGHT, 0, 0)
        root.setSpacing(0)
        root.addWidget(container)

        self._switch_anim: QPropertyAnimation | None = None

    def switch_page(self, index: int) -> None:
        """切换页面，附带 250ms 淡入动画（§7.1）。"""
        widget = self.stack.widget(index)
        self.stack.setCurrentIndex(index)

        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        self._switch_anim = QPropertyAnimation(effect, b"opacity", self)
        self._switch_anim.setDuration(Duration.PAGE_SWITCH)
        self._switch_anim.setStartValue(0.0)
        self._switch_anim.setEndValue(1.0)
        self._switch_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._switch_anim.finished.connect(lambda: widget.setGraphicsEffect(None))
        self._switch_anim.start()
