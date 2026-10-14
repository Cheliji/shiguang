"""日记页（模块二实现）。"""

from shiguang.ui.pages.base import PlaceholderPage


class DiaryPage(PlaceholderPage):
    def __init__(self, parent=None) -> None:
        super().__init__("日记 · 模块建设中", parent)
