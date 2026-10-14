"""今日首页（规格：UI 设计文档 §4.1）。

结构：顶部功能区（状态表情 + 励志文案 + 操作按钮）→ DateBar → 概览卡片区 →
今日代办列表（逾期置顶分组）→ 通栏"添加今日代办"按钮。空状态见 §6.1。

接线说明：新建/编辑弹窗属 T10，归档弹窗属 T13，本任务按钮先占位提示。
"""

import random
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import InfoBar, InfoBarPosition

from shiguang.services import get_task_service
from shiguang.ui.theme import Color, FontSize, Space
from shiguang.ui.widgets.buttons import ghost_button, primary_button, secondary_button
from shiguang.ui.widgets.date_bar import DateBar
from shiguang.ui.widgets.task_card import TaskCard

PHRASES = [
    "今天也是充满希望的一天",
    "认真做好每一件小事",
    "以质量取胜，而不是以量取胜",
    "完成比完美更重要",
    "日积月累，功不唐捐",
]


def mood_emoji(rate: float) -> str:
    """按完成率返回状态表情（§4.1.2）。"""
    if rate >= 1.0:
        return "🎉"
    if rate > 0.6:
        return "😊"
    if rate > 0.3:
        return "🙂"
    if rate > 0:
        return "☕"
    return "🌱"


class _StatCard(QFrame):
    """概览卡片容器（§4.1.4）。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"_StatCard {{ background: {Color.SURFACE}; border-radius: 12px; }}")


class TodayPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = get_task_service()
        self._selected_date = date.today()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet(f"background: {Color.BG_PRIMARY};")
        scroll.setWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(Space.XL, Space.XL, Space.XL, Space.XL)
        layout.setSpacing(Space.LG)

        layout.addLayout(self._build_top_bar())
        layout.addWidget(self._build_date_bar())

        cards_row = QHBoxLayout()
        cards_row.setSpacing(Space.LG)
        cards_row.addWidget(self._build_todo_stat_card(), 1)
        cards_row.addWidget(self._build_diary_card(), 1)
        layout.addLayout(cards_row)

        layout.addWidget(self._build_list_header())
        layout.addLayout(self._build_list_area())
        layout.addWidget(self._build_add_button())
        layout.addStretch(1)

        self._service.changed.connect(self.refresh)
        self.refresh()

    # ---------- 区块构建 ----------
    def _build_top_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.setContentsMargins(0, 0, 0, 0)

        self.mood_label = QLabel()
        self.mood_label.setStyleSheet("font-size: 32px;")
        bar.addWidget(self.mood_label)

        self.phrase_label = QLabel(random.choice(PHRASES))
        self.phrase_label.setStyleSheet(
            f"color: {Color.TEXT_SECONDARY}; font-size: {FontSize.BODY}px;"
        )
        bar.addWidget(self.phrase_label, 0, Qt.AlignmentFlag.AlignVCenter)
        bar.addSpacing(Space.LG)
        bar.addStretch(1)

        self.new_button = primary_button("新建代办", "plus", self)
        self.new_button.clicked.connect(self._on_new_clicked)
        bar.addWidget(self.new_button)

        diary_button = secondary_button("写日记", "book-open", self)
        diary_button.clicked.connect(self._on_diary_clicked)
        bar.addWidget(diary_button)
        return bar

    def _build_date_bar(self) -> DateBar:
        self.date_bar = DateBar(self)
        self.date_bar.date_selected.connect(self._on_date_selected)
        return self.date_bar

    def _build_todo_stat_card(self) -> QFrame:
        card = _StatCard(self)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(Space.LG, Space.LG, Space.LG, Space.LG)
        layout.setSpacing(Space.SM)

        header = QHBoxLayout()
        title = QLabel("📝 今日代办")
        title.setStyleSheet(f"color: {Color.TEXT_SECONDARY}; font-size: {FontSize.AUXILIARY}px;")
        header.addWidget(title)
        header.addStretch(1)
        layout.addLayout(header)

        self.stat_number = QLabel("0 个待完成")
        self.stat_number.setStyleSheet(f"font-size: {FontSize.NUMBER}px; font-weight: 300;")
        layout.addWidget(self.stat_number)

        self.stat_progress = QProgressBar()
        self.stat_progress.setRange(0, 100)
        self.stat_progress.setTextVisible(False)
        self.stat_progress.setFixedHeight(6)
        self.stat_progress.setStyleSheet(
            f"QProgressBar {{ background: {Color.BG_SECONDARY};"
            " border-radius: 3px; border: none; }"
            f"QProgressBar::chunk {{ background: {Color.PRIMARY}; border-radius: 3px; }}"
        )
        layout.addWidget(self.stat_progress)
        return card

    def _build_diary_card(self) -> QFrame:
        """日记状态卡片（占位：模块二接线）。"""
        card = _StatCard(self)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(Space.LG, Space.LG, Space.LG, Space.LG)
        layout.setSpacing(Space.SM)

        title = QLabel("📓 今日日记")
        title.setStyleSheet(f"color: {Color.TEXT_SECONDARY}; font-size: {FontSize.AUXILIARY}px;")
        layout.addWidget(title)

        status = QLabel("未记录")
        status.setStyleSheet("font-size: 18px; font-weight: 500;")
        layout.addWidget(status)

        hint = QLabel("点击记录今日复盘")
        hint.setStyleSheet(f"color: {Color.TEXT_TERTIARY}; font-size: {FontSize.TINY}px;")
        layout.addWidget(hint)

        button = ghost_button("去写日记", parent=card)
        button.clicked.connect(self._on_diary_clicked)
        layout.addWidget(button, 0, Qt.AlignmentFlag.AlignLeft)
        return card

    def _build_list_header(self) -> QWidget:
        holder = QWidget(self)
        row = QHBoxLayout(holder)
        row.setContentsMargins(0, 0, 0, 0)

        self.list_title = QLabel("今日代办")
        self.list_title.setStyleSheet("font-size: 18px; font-weight: 500;")
        row.addWidget(self.list_title)

        self.count_badge = QLabel("0")
        self.count_badge.setStyleSheet(
            f"background: {Color.PRIMARY_LIGHT}; color: {Color.PRIMARY};"
            f"border-radius: 9px; padding: 2px 10px; font-size: {FontSize.TINY}px;"
        )
        row.addWidget(self.count_badge)
        row.addStretch(1)
        return holder

    def _build_list_area(self) -> QVBoxLayout:
        self.list_layout = QVBoxLayout()
        self.list_layout.setSpacing(Space.SM)
        return self.list_layout

    def _build_add_button(self) -> QWidget:
        button = primary_button("＋ 添加今日代办", parent=self)
        button.setFixedHeight(48)
        button.setStyleSheet(
            f"QPushButton {{ background: {Color.BG_SECONDARY}; color: {Color.TEXT_PRIMARY};"
            f" border: none; border-radius: 12px; font-size: {FontSize.BODY}px; }}"
            f"QPushButton:hover {{ background: #E5E7EB; }}"
        )
        button.clicked.connect(self._on_new_clicked)
        return button

    # ---------- 刷新 ----------
    def refresh(self) -> None:
        day = self._selected_date
        summary = self._service.today_summary(day)

        self.mood_label.setText(mood_emoji(summary.rate))
        self.stat_number.setText(f"{summary.total - summary.archived} 个待完成")
        self.stat_progress.setValue(int(summary.rate * 100))

        today = date.today()
        self.list_title.setText("今日代办" if day == today else day.strftime("%m-%d 代办"))

        # DateBar 圆点
        self.date_bar.set_todo_dates(self._service.list_todo_dates())

        # 列表：今日视图下逾期置顶分组
        overdue = self._service.list_overdue() if day == today else []
        items = self._service.list_today(day)
        self.count_badge.setText(str(len(items) + len(overdue)))

        self._clear_list()
        if not overdue and not items:
            self._add_empty_state()
            return

        if overdue:
            header = QLabel(f"⚠ 逾期未处理（{len(overdue)}）")
            header.setStyleSheet(
                f"color: {Color.DANGER}; font-size: {FontSize.AUXILIARY}px; font-weight: 500;"
            )
            self.list_layout.addWidget(header)
            for item in overdue:
                self._add_card(item)
        for item in items:
            self._add_card(item)

    def _clear_list(self) -> None:
        while self.list_layout.count():
            child = self.list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _add_card(self, item) -> None:
        card = TaskCard(self)
        card.set_data(item)
        # 归档弹窗接线属 T13；编辑弹窗属 T10
        card.edit_requested.connect(self._on_edit_placeholder)
        self.list_layout.addWidget(card)

    def _add_empty_state(self) -> None:
        holder = QWidget(self)
        box = QVBoxLayout(holder)
        box.setContentsMargins(0, Space.XXXL, 0, Space.XXXL)
        box.setSpacing(Space.SM)
        icon = QLabel("📝")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 48px;")
        main = QLabel("今天还没有代办")
        main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.setStyleSheet("font-size: 18px; font-weight: 500;")
        sub = QLabel("添加一个代办，开始高效的一天")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"color: {Color.TEXT_SECONDARY}; font-size: {FontSize.BODY}px;")
        box.addWidget(icon)
        box.addWidget(main)
        box.addWidget(sub)
        self.list_layout.addWidget(holder)

    # ---------- 交互 ----------
    def _on_date_selected(self, day: date) -> None:
        self._selected_date = day
        self.refresh()

    def _on_new_clicked(self) -> None:
        # T10：打开创建对话框
        InfoBar.info(
            "提示", "创建对话框将在 T10 接入", parent=self.window(), position=InfoBarPosition.TOP
        )

    def _on_edit_placeholder(self, task_id: int) -> None:
        InfoBar.info(
            "提示", "编辑对话框将在 T10 接入", parent=self.window(), position=InfoBarPosition.TOP
        )

    def _on_diary_clicked(self) -> None:
        InfoBar.info(
            "提示", "日记模块建设中（模块二）", parent=self.window(), position=InfoBarPosition.TOP
        )
