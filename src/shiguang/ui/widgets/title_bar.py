"""自绘标题栏（UI 制作要求 #2：禁止原生标题栏，规格见 UI 设计文档 §3.3）。

基于 qframelesswindow 的 StandardTitleBar（自带无边框拖拽、双击最大化、
最小化/最大化/关闭自绘按钮），按 §3.3 定制高度、Logo、标题与配色。
"""

from qframelesswindow import StandardTitleBar

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


class AppTitleBar(StandardTitleBar):
    """拾光标题栏：左侧 Logo + "拾光"，右侧最小化/最大化/关闭（自绘）。

    关闭按钮悬停红底由 qfluentwidgets 默认提供；拖拽移动与双击最大化
    由 StandardTitleBar 基类提供。
    """

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setFixedHeight(Layout.TITLE_BAR_HEIGHT)

        # 左侧 Logo（16px，主色风筝占位图标——正式 Logo 后续任务再定）
        self.iconLabel.setPixmap(colored_pixmap("target", Color.PRIMARY, 16))
        self.iconLabel.setFixedSize(16, 16)
        self.titleLabel.setText("拾光")

        self.setStyleSheet(_TITLE_BAR_QSS)
