"""代办列表页（规格：UI 设计文档 §4.2）。

标题区 + Pill 筛选标签（今日/待办/逾期/已归档）+ 日期筛选下拉 + 列表 + 分场景空状态。
"""

from datetime import date, timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import InfoBar, InfoBarPosition

from shiguang.services import get_task_service
from shiguang.services.dto import TodoItem
from shiguang.ui.theme import Color, FontSize, Space
from shiguang.ui.widgets.buttons import primary_button
from shiguang.ui.widgets.task_card import TaskCard

TAB_LABELS = ["今日", "待办", "逾期", "已归档"]
DATE_FILTERS = ["全部日期", "今天", "最近7天", "最近30天"]

_PILL_QSS = f"""
QPushButton {{
    background: transparent; color: {Color.TEXT_SECONDARY};
    border: none; border-radius: 8px; padding: 6px 16px;
    font-size: {FontSize.BODY}px;
}}
QPushButton:hover {{ background: {Color.BG_PRIMARY}; }}
QPushButton:checked {{
    background: {Color.PRIMARY_LIGHT}; color: {Color.PRIMARY}; font-weight: 500;
}}
"""


class TodoPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = get_task_service()
        self._items: dict[int, TodoItem] = {}
        self._current_tab = 0

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

        layout.addLayout(self._build_header())
        layout.addWidget(self._build_filter_bar())

        self.list_layout = QVBoxLayout()
        self.list_layout.setSpacing(Space.SM)
        layout.addLayout(self.list_layout)
        layout.addStretch(1)

        self._service.changed.connect(self.refresh)
        self.refresh()

    # ---------- 区块 ----------
    def _build_header(self) -> QHBoxLayout:
        row = QHBoxLayout()
        title = QLabel("代办")
        title.setStyleSheet("font-size: 24px; font-weight: 600;")
        row.addWidget(title)
        row.addStretch(1)
        self.new_button = primary_button("新建代办", "plus", self)
        self.new_button.clicked.connect(self._on_new)
        row.addWidget(self.new_button)
        return row

    def _build_filter_bar(self) -> QFrame:
        bar = QFrame(self)
        bar.setStyleSheet(f"QFrame {{ background: {Color.SURFACE}; border-radius: 12px; }}")
        row = QHBoxLayout(bar)
        row.setContentsMargins(Space.LG, Space.SM, Space.LG, Space.SM)
        row.setSpacing(Space.XS)

        self.tab_group = QButtonGroup(bar)
        self.tab_group.setExclusive(True)
        self.tab_buttons: list[QPushButton] = []
        for i, label in enumerate(TAB_LABELS):
            button = QPushButton(label, bar)
            button.setCheckable(True)
            button.setStyleSheet(_PILL_QSS)
            button.clicked.connect(lambda checked=False, idx=i: self._on_tab_changed(idx))
            self.tab_group.addButton(button, i)
            row.addWidget(button)
            self.tab_buttons.append(button)
        self.tab_buttons[0].setChecked(True)

        row.addStretch(1)

        self.date_filter = QComboBox(bar)
        for label in DATE_FILTERS:
            self.date_filter.addItem(label)
        self.date_filter.setFixedHeight(36)
        self.date_filter.setStyleSheet(
            f"QComboBox {{ background: {Color.SURFACE}; border: 1px solid {Color.BG_SECONDARY};"
            f" border-radius: 8px; padding: 6px 12px; font-size: {FontSize.BODY}px; }}"
        )
        self.date_filter.currentIndexChanged.connect(self.refresh)
        row.addWidget(self.date_filter)
        return bar

    # ---------- 数据 ----------
    def _filter_by_date(self, items: list[TodoItem], use_archived: bool) -> list[TodoItem]:
        mode = self.date_filter.currentIndex()
        if mode == 0:  # 全部日期
            return items
        today = date.today()
        if mode == 1:  # 今天
            if use_archived:
                return [i for i in items if i.archived_at and i.archived_at.date() == today]
            return [i for i in items if i.date == today]
        if mode == 2:  # 最近7天
            start = today - timedelta(days=6)
        else:  # 最近30天
            start = today - timedelta(days=29)
        if use_archived:
            return [i for i in items if i.archived_at and start <= i.archived_at.date() <= today]
        return [i for i in items if i.date and start <= i.date <= today]

    def refresh(self) -> None:
        tab = self._current_tab
        today = date.today()
        self._items.clear()
        self._clear_list()

        if tab == 0:  # 今日
            overdue = self._service.list_overdue()
            items = self._service.list_today(today)
            all_items = overdue + items
            if not all_items:
                self._empty("今天还没有代办", "添加一个代办，开始高效的一天")
                return
            if overdue:
                self._group_header(f"⚠ 逾期未处理（{len(overdue)}）", Color.DANGER)
                for item in overdue:
                    self._add_card(item)
            for item in items:
                self._add_card(item)

        elif tab == 1:  # 待办
            items = self._filter_by_date(self._service.list_pending(), use_archived=False)
            if not items:
                self._empty("没有找到匹配的代办", "尝试调整筛选条件")
                return
            # 按日期分组
            groups: dict[date, list[TodoItem]] = {}
            for item in items:
                groups.setdefault(item.date or date.max, []).append(item)
            for day in sorted(groups):
                header = "今天" if day == today else day.strftime("%m-%d")
                self._group_header(header, Color.TEXT_SECONDARY)
                for item in groups[day]:
                    self._add_card(item)

        elif tab == 2:  # 逾期
            items = self._service.list_overdue()
            if not items:
                self._empty("暂无逾期代办", "太棒了，全部按时完成！")
                return
            for item in items:
                self._add_card(item)

        else:  # 已归档
            items = self._filter_by_date(self._service.list_archived(), use_archived=True)
            if not items:
                self._empty("还没有归档记录", "完成任务并归档，积累成就感")
                return
            for item in items:
                self._add_card(item)

    def _clear_list(self) -> None:
        while self.list_layout.count():
            child = self.list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _group_header(self, text: str, color: str) -> None:
        label = QLabel(text)
        label.setStyleSheet(f"color: {color}; font-size: {FontSize.AUXILIARY}px; font-weight: 500;")
        self.list_layout.addWidget(label)

    def _add_card(self, item: TodoItem) -> None:
        self._items[item.id] = item
        card = TaskCard(self)
        card.set_data(item)
        card.archive_requested.connect(self._on_archive)
        card.edit_requested.connect(self._on_edit)
        card.delete_requested.connect(self._on_delete)
        card.details_requested.connect(self._on_details)
        self.list_layout.addWidget(card)

    def _empty(self, title: str, subtitle: str) -> None:
        holder = QWidget(self)
        box = QVBoxLayout(holder)
        box.setContentsMargins(0, Space.XXXL, 0, Space.XXXL)
        box.setSpacing(Space.SM)
        icon = QLabel("📭")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 48px;")
        main = QLabel(title)
        main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.setStyleSheet("font-size: 18px; font-weight: 500;")
        sub = QLabel(subtitle)
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"color: {Color.TEXT_SECONDARY}; font-size: {FontSize.BODY}px;")
        box.addWidget(icon)
        box.addWidget(main)
        box.addWidget(sub)
        self.list_layout.addWidget(holder)

    # ---------- 交互 ----------
    def _on_tab_changed(self, index: int) -> None:
        self._current_tab = index
        self.refresh()

    def _on_new(self) -> None:
        from shiguang.ui.dialogs.todo_dialog import TodoDialog

        dialog = TodoDialog(self.window())
        if dialog.exec():
            data = dialog.get_data()
            if data["repeat"] != "none" and "day" not in data:
                data["day"] = date.today()
            try:
                self._service.create_todo(**data)
                InfoBar.success(
                    "成功", "代办已创建", parent=self.window(), position=InfoBarPosition.TOP
                )
            except ValueError as e:
                InfoBar.error("失败", str(e), parent=self.window(), position=InfoBarPosition.TOP)

    def _on_archive(self, task_id: int) -> None:
        from shiguang.ui.dialogs.archive_dialog import ArchiveDialog

        item = self._items.get(task_id)
        if item is None:
            return
        dialog = ArchiveDialog(self.window(), item=item)
        if dialog.exec():
            try:
                self._service.archive(task_id, dialog.get_data())
                InfoBar.success(
                    "成功", "已归档，干得漂亮！", parent=self.window(), position=InfoBarPosition.TOP
                )
            except ValueError as e:
                InfoBar.error("失败", str(e), parent=self.window(), position=InfoBarPosition.TOP)

    def _on_edit(self, task_id: int) -> None:
        from shiguang.ui.dialogs.todo_dialog import TodoDialog

        item = self._items.get(task_id)
        if item is None:
            return
        dialog = TodoDialog(self.window(), item=item)
        if dialog.exec():
            try:
                self._service.update_todo(task_id, **dialog.get_data())
                InfoBar.success(
                    "成功", "代办已保存", parent=self.window(), position=InfoBarPosition.TOP
                )
            except ValueError as e:
                InfoBar.error("失败", str(e), parent=self.window(), position=InfoBarPosition.TOP)

    def _on_delete(self, task_id: int) -> None:
        from qfluentwidgets import MessageBox

        item = self._items.get(task_id)
        if item is None:
            return
        box = MessageBox("删除代办", f"确定删除『{item.name}』？", self.window())
        box.yesButton.setText("删除")
        box.cancelButton.setText("取消")
        if box.exec():
            try:
                self._service.delete_todo(task_id)
                InfoBar.success(
                    "成功", "代办已删除", parent=self.window(), position=InfoBarPosition.TOP
                )
            except ValueError as e:
                InfoBar.error("失败", str(e), parent=self.window(), position=InfoBarPosition.TOP)

    def _on_details(self, task_id: int) -> None:
        from shiguang.ui.dialogs.archive_detail_dialog import ArchiveDetailDialog

        item = self._items.get(task_id)
        if item is None:
            return
        dialog = ArchiveDetailDialog(self.window(), item=item)
        dialog.exec()
