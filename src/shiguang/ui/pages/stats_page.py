"""统计页（模块三实现）。"""

from shiguang.ui.pages.base import PlaceholderPage


class StatsPage(PlaceholderPage):
    def __init__(self, parent=None) -> None:
        super().__init__("统计 · 模块建设中", parent)
