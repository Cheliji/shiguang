"""自绘标题栏（UI 制作要求 #2：禁止原生标题栏，规格见 UI 设计文档 §3.3）。

基于 qframelesswindow 的 StandardTitleBar（自带无边框拖拽、双击最大化、
最小化/最大化/关闭自绘按钮），按 §3.3 定制高度、Logo、标题与配色。

系统按钮定制（`Stretch*Button`）：qframelesswindow 原生的按钮固定 46x32，
悬停底色只覆盖按钮自身矩形，在 40px 标题栏中上下各留一条白边。这里把按钮
高度撑满标题栏（悬停底色自然延伸至上/下/右边缘，类原生窗口体验），并重绘
图标使其在新高度下保持垂直居中（关闭按钮的 SVG 按整个矩形渲染，自动居中）。
"""

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainter, QPainterPath, QPen
from qframelesswindow import StandardTitleBar
from qframelesswindow.titlebar.title_bar_buttons import (
    CloseButton,
    MaximizeButton,
    MinimizeButton,
)
from qframelesswindow.utils import toggleMaxState

from shiguang.ui.icons import colored_pixmap
from shiguang.ui.theme import Color, Layout

_TITLE_BAR_QSS = f"""
StandardTitleBar {{
    background: {Color.SURFACE};
    border-bottom: 1px solid {Color.BG_SECONDARY};
}}
StandardTitleBar > QLabel#titleLabel {{
    font-size: 14px;
    font-weight: 500;
    color: {Color.TEXT_PRIMARY};
}}
"""


class StretchMinimizeButton(MinimizeButton):
    """最小化按钮：高度撑满标题栏，悬停底色延伸至上下边框。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(Layout.TITLE_BAR_HEIGHT)

    def paintEvent(self, e) -> None:
        painter = QPainter(self)
        color, bgColor = self._getColors()

        # 悬停/按下底色铺满整个按钮（= 标题栏高度），延伸至上下边缘
        painter.setBrush(bgColor)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())

        # 图标垂直居中（原生坐标按 32px 高度、中线 16px 绘制）
        painter.setBrush(Qt.BrushStyle.NoBrush)
        pen = QPen(color, 1)
        pen.setCosmetic(True)
        painter.setPen(pen)
        center_y = self.height() // 2
        painter.drawLine(18, center_y, 28, center_y)


class StretchMaximizeButton(MaximizeButton):
    """最大化/还原按钮：高度撑满标题栏，悬停底色延伸至上下边框。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(Layout.TITLE_BAR_HEIGHT)

    def paintEvent(self, e) -> None:
        painter = QPainter(self)
        color, bgColor = self._getColors()

        painter.setBrush(bgColor)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())

        painter.setBrush(Qt.BrushStyle.NoBrush)
        pen = QPen(color, 1)
        pen.setCosmetic(True)
        painter.setPen(pen)

        # 原生图标按 32px 高度居中（中线 16px），整体下移保持垂直居中
        dy = self.height() // 2 - 16
        r = self.devicePixelRatioF()
        painter.scale(1 / r, 1 / r)
        if not self._isMax:
            painter.drawRect(int(18 * r), int((11 + dy) * r), int(10 * r), int(10 * r))
        else:
            painter.drawRect(int(18 * r), int((13 + dy) * r), int(8 * r), int(8 * r))
            x0 = int(18 * r) + int(2 * r)
            y0 = (13 + dy) * r
            dw = int(2 * r)
            path = QPainterPath(QPointF(x0, y0))
            path.lineTo(x0, y0 - dw)
            path.lineTo(x0 + 8 * r, y0 - dw)
            path.lineTo(x0 + 8 * r, y0 - dw + 8 * r)
            path.lineTo(x0 + 8 * r - dw, y0 - dw + 8 * r)
            painter.drawPath(path)


class StretchCloseButton(CloseButton):
    """关闭按钮：高度撑满标题栏；SVG 图标按按钮矩形渲染，自动居中。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(Layout.TITLE_BAR_HEIGHT)


class AppTitleBar(StandardTitleBar):
    """拾光标题栏：左侧 Logo + "拾光"，右侧最小化/最大化/关闭（自绘）。

    关闭按钮悬停红底、拖拽移动与双击最大化由 qframelesswindow 提供；
    三个系统按钮替换为 Stretch* 版本，悬停底色延伸至标题栏边缘。
    """

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setFixedHeight(Layout.TITLE_BAR_HEIGHT)

        # 左侧 Logo（16px，主色风筝占位图标——正式 Logo 后续任务再定）
        self.iconLabel.setPixmap(colored_pixmap("target", Color.PRIMARY, 16))
        self.iconLabel.setFixedSize(16, 16)
        self.titleLabel.setText("拾光")

        # 替换系统按钮：撑满标题栏高度，悬停底色延伸至上/下/右边缘
        for old in (self.minBtn, self.maxBtn, self.closeBtn):
            self.hBoxLayout.removeWidget(old)
            old.deleteLater()
        self.minBtn = StretchMinimizeButton(self)
        self.maxBtn = StretchMaximizeButton(self)
        self.closeBtn = StretchCloseButton(self)
        self.minBtn.clicked.connect(self.window().showMinimized)
        self.maxBtn.clicked.connect(self._toggle_max_state)
        self.closeBtn.clicked.connect(self.window().close)
        self.hBoxLayout.addWidget(self.minBtn, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addWidget(self.maxBtn, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addWidget(self.closeBtn, 0, Qt.AlignmentFlag.AlignRight)

        self.setStyleSheet(_TITLE_BAR_QSS)

    def _toggle_max_state(self) -> None:
        toggleMaxState(self.window())
