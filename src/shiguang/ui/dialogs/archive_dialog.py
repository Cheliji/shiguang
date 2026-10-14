"""归档弹窗（规格：UI 设计文档 §4.4）——拾光核心"留痕"仪式。

结构：只读任务信息卡（含完成标准子卡）→ 分隔线 → 归档信息区
（用时 + 快捷标签 / 评分 + 标签 / 总结可选 + 字数统计）→ 绿色确认按钮。
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QToolButton, QVBoxLayout, QWidget
from qfluentwidgets import MessageBoxBase, SpinBox, TextEdit

from shiguang.services.dto import ArchiveInput, TodoItem
from shiguang.ui.icons import colored_icon
from shiguang.ui.theme import Color, FontSize, Space
from shiguang.ui.widgets.rating_widget import RatingWidget

QUICK_DURATIONS = [15, 30, 45, 60, 90]
SUMMARY_LIMIT = 500

_PILL_QSS = f"""
QPushButton {{
    background: {Color.SURFACE}; color: {Color.TEXT_SECONDARY};
    border: 1px solid {Color.BG_SECONDARY}; border-radius: 8px;
    padding: 4px 12px; font-size: {FontSize.AUXILIARY}px;
}}
QPushButton:checked {{
    background: {Color.PRIMARY}; color: #FFFFFF; border: 1px solid {Color.PRIMARY};
}}
"""


class ArchiveDialog(MessageBoxBase):
    """代办归档弹窗。确认后调用方通过 get_data() 取 ArchiveInput。"""

    def __init__(self, parent: QWidget | None = None, item: TodoItem | None = None) -> None:
        super().__init__(parent)
        self._item = item
        self.widget.setFixedWidth(580)

        # 标题行
        title_row = QHBoxLayout()
        title = QLabel("归档代办")
        title.setStyleSheet("font-size: 16px; font-weight: 600;")
        close_button = QToolButton(self.widget)
        close_button.setIcon(colored_icon("x", Color.TEXT_SECONDARY, 16))
        close_button.setFixedSize(24, 24)
        close_button.setStyleSheet(
            "QToolButton { border: none; border-radius: 4px; }"
            f"QToolButton:hover {{ background: {Color.DANGER_LIGHT}; }}"
        )
        close_button.clicked.connect(self.reject)
        title_row.addWidget(title)
        title_row.addStretch(1)
        title_row.addWidget(close_button)
        self.viewLayout.addLayout(title_row)

        # 原始任务信息（只读）
        self.viewLayout.addWidget(self._build_info_card())

        # 分隔线
        divider = QWidget(self.widget)
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background: {Color.BG_SECONDARY};")
        self.viewLayout.addWidget(divider)

        # 归档信息 *
        section = QLabel("归档信息 *")
        section.setStyleSheet(f"font-size: {FontSize.BODY}px; font-weight: 600;")
        self.viewLayout.addWidget(section)

        # 代办用时
        self.viewLayout.addLayout(self._field_label("代办用时（分钟）", required=True))
        duration_row = QHBoxLayout()
        duration_row.setSpacing(Space.SM)
        self.duration_spin = SpinBox(self.widget)
        self.duration_spin.setRange(1, 100000)
        self.duration_spin.setValue(30)
        self.duration_spin.setFixedHeight(44)
        self.duration_spin.valueChanged.connect(self._update_confirm_enabled)
        duration_row.addWidget(self.duration_spin)
        duration_row.addStretch(1)
        self.viewLayout.addLayout(duration_row)

        quick_row = QHBoxLayout()
        quick_row.setSpacing(Space.SM)
        for minutes in QUICK_DURATIONS:
            pill = QPushButton(f"{minutes}分钟", self.widget)
            pill.setCheckable(True)
            pill.setStyleSheet(_PILL_QSS)
            pill.clicked.connect(lambda checked=False, m=minutes: self._on_quick_duration(m))
            quick_row.addWidget(pill)
            self._duration_pills = getattr(self, "_duration_pills", []) + [pill]
        quick_row.addStretch(1)
        self.viewLayout.addLayout(quick_row)

        # 质量评分
        self.viewLayout.addLayout(self._field_label("质量评分", required=True))
        self.rating = RatingWidget(size=28, show_label=True, parent=self.widget)
        self.rating.score_changed.connect(self._update_confirm_enabled)
        self.viewLayout.addWidget(self.rating, 0, Qt.AlignmentFlag.AlignLeft)

        # 总结（可选）
        self.viewLayout.addLayout(self._field_label("总结（可选）"))
        self.summary_edit = TextEdit(self.widget)
        self.summary_edit.setPlaceholderText("这次完成得怎么样？有什么可以复用的经验？")
        self.summary_edit.setFixedHeight(120)
        self.viewLayout.addWidget(self.summary_edit)
        self.counter_label = QLabel("已输入 0/500 字")
        self.counter_label.setStyleSheet(
            f"color: {Color.TEXT_TERTIARY}; font-size: {FontSize.TINY}px;"
        )
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.viewLayout.addWidget(self.counter_label)
        self.summary_edit.textChanged.connect(self._update_counter)

        # 按钮
        self.yesButton.setText("✓ 确认归档")
        self.yesButton.setStyleSheet(
            "QPushButton { background: #10B981; color: #FFFFFF; border: none;"
            " border-radius: 8px; padding: 0 24px; font-size: 14px; font-weight: 500; }"
            "QPushButton:hover { background: #0DA271; }"
            "QPushButton:disabled { background: #D1D5DB; color: #9CA3AF; }"
        )
        self.yesButton.setFixedHeight(44)
        self.cancelButton.setText("取消")

        if item:
            self.name_label.setText(item.name)
            self.desc_label.setText(item.description or "无描述")
            self.standard_text.setText(item.standard or "无完成标准")

        self._update_counter()
        self._update_confirm_enabled()

    # ---------- 区块 ----------
    def _build_info_card(self) -> QWidget:
        """只读任务信息卡（§4.4.3）。"""
        card = QWidget(self.widget)
        card.setStyleSheet(f"background: {Color.BG_PRIMARY}; border-radius: 12px;")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(Space.LG, Space.LG, Space.LG, Space.LG)
        layout.setSpacing(Space.SM)

        header = QLabel("📋 原始任务信息（只读）")
        header.setStyleSheet(
            f"color: {Color.TEXT_SECONDARY}; font-size: {FontSize.AUXILIARY}px; font-weight: 500;"
        )
        layout.addWidget(header)

        self.name_label = QLabel()
        self.name_label.setStyleSheet(f"font-size: {FontSize.BODY}px; font-weight: 500;")
        layout.addWidget(self.name_label)

        self.desc_label = QLabel()
        self.desc_label.setStyleSheet(
            f"color: {Color.TEXT_SECONDARY}; font-size: {FontSize.AUXILIARY}px;"
        )
        layout.addWidget(self.desc_label)

        # 完成标准子卡（白底 + 左侧 4px 主色竖条）
        sub = QWidget(card)
        sub.setStyleSheet(
            f"background: {Color.SURFACE}; border-left: 4px solid {Color.PRIMARY};"
            " border-radius: 8px;"
        )
        sub_layout = QVBoxLayout(sub)
        sub_layout.setContentsMargins(Space.MD, Space.MD, Space.MD, Space.MD)
        sub_layout.setSpacing(4)
        self.standard_text = QLabel()
        self.standard_text.setWordWrap(True)
        self.standard_text.setStyleSheet(
            f"font-size: {FontSize.BODY}px; font-weight: 500; color: {Color.TEXT_PRIMARY};"
        )
        sub_layout.addWidget(self.standard_text)
        hint = QLabel("对照此标准，确认任务完成质量后再归档")
        hint.setStyleSheet(f"color: {Color.TEXT_TERTIARY}; font-size: {FontSize.TINY}px;")
        sub_layout.addWidget(hint)
        layout.addWidget(sub)
        return card

    def _field_label(self, text: str, required: bool = False) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, Space.SM, 0, 0)
        label = QLabel(f'{text} <span style="color:{Color.DANGER}">*</span>' if required else text)
        label.setStyleSheet(f"font-size: {FontSize.BODY}px; font-weight: 500;")
        row.addWidget(label)
        row.addStretch(1)
        return row

    # ---------- 交互 ----------
    def _on_quick_duration(self, minutes: int) -> None:
        self.duration_spin.setValue(minutes)
        for pill in self._duration_pills:
            pill.setChecked(pill.text() == f"{minutes}分钟")

    def _update_counter(self) -> None:
        length = len(self.summary_edit.toPlainText())
        color = Color.WARNING if length > 450 else Color.TEXT_TERTIARY
        self.counter_label.setText(f"已输入 {length}/{SUMMARY_LIMIT} 字")
        self.counter_label.setStyleSheet(f"color: {color}; font-size: {FontSize.TINY}px;")

    def _update_confirm_enabled(self) -> None:
        """评分 + 用时必填（§4.4.3 禁用态）。"""
        self.yesButton.setEnabled(self.rating.score() > 0 and self.duration_spin.value() > 0)

    def validate(self) -> bool:
        return self.rating.score() > 0 and self.duration_spin.value() > 0

    # ---------- 数据 ----------
    def get_data(self) -> ArchiveInput:
        return ArchiveInput(
            duration=self.duration_spin.value(),
            score=self.rating.score(),
            summary=self.summary_edit.toPlainText().strip(),
        )

    def task_id(self) -> int | None:
        return self._item.id if self._item else None
