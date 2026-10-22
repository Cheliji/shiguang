"""代办创建/编辑对话框（规格：UI 设计文档 §4.3）。

T10：名称/描述/完成标准（必填校验）。
T24：重复周期 + 日期联动（v1.3 §4.3.3）：不重复→计划日期；每日/每周/每月→
「开始日期 + 结束日期」（均必填），附生成条数实时预览，校验失败禁用确认按钮。
T12：延期策略单选组 + 关联目标占位（禁用）。

重写要点（对齐 §4.3.1/§4.3.2 与 AGENT.md「UI 样式规则」）：
- 表单内容放入 QScrollArea（§4.3.1：最大高度 680px，超出内部滚动），字段不再被挤压；
- 字段顺序严格按 §4.3.2：名称 → 重复周期+计划日期 → 延期策略 → 关联目标 → 描述 → 完成标准；
- 下拉箭头使用 Feather chevron-down 矢量图标（ChevronComboBox），不使用 Qt 原生箭头；
- 容器背景一律经 set_container_bg / 限定选择器，禁止无选择器 background（§9.3.1）。
"""

from datetime import date

from PySide6.QtCore import QDate, QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import LineEdit, MessageBoxBase

from shiguang.domain.rules import expand_dates
from shiguang.services.dto import (
    REPEAT_DAILY,
    REPEAT_LABELS,
    REPEAT_MONTHLY,
    REPEAT_NONE,
    REPEAT_WEEKLY,
    TodoItem,
)
from shiguang.ui.icons import colored_icon
from shiguang.ui.theme import Color, FontSize, Space
from shiguang.ui.widgets.date_picker import DatePickerButton
from shiguang.ui.widgets.form_fields import AutoGrowTextEdit, ChevronComboBox, DialogScrollArea

_FIELD_QSS = f"""
LineEdit, TextEdit, QComboBox {{
    background: {Color.SURFACE};
    border: 1px solid {Color.BG_SECONDARY};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: {FontSize.BODY}px;
}}
LineEdit:focus, TextEdit:focus {{
    border: 1px solid {Color.PRIMARY};
}}
{ChevronComboBox.arrow_qss()}
"""

_ERROR_QSS = f"""
LineEdit, TextEdit {{
    background: {Color.SURFACE};
    border: 1px solid {Color.DANGER};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: {FontSize.BODY}px;
}}
"""

_RADIO_QSS = f"""
QRadioButton {{
    font-size: {FontSize.BODY}px;
    color: {Color.TEXT_PRIMARY};
    spacing: 6px;
}}
QRadioButton::indicator {{
    width: 16px;
    height: 16px;
}}
"""

# §4.3.1：弹窗最大高度 680px，超出内部滚动
_DIALOG_MAX_HEIGHT = 680


class TodoDialog(MessageBoxBase):
    """创建/编辑代办对话框。校验通过后 accept()，调用方用 get_data() 取数据。"""

    def __init__(self, parent: QWidget | None = None, item: TodoItem | None = None) -> None:
        super().__init__(parent)
        self._item = item
        self._editing_repeat = bool(item and item.repeat != REPEAT_NONE)
        self.widget.setFixedWidth(520)
        self.widget.setMaximumHeight(_DIALOG_MAX_HEIGHT)
        self._unify_background()

        # 标题行
        title_row = QHBoxLayout()
        title = QLabel("编辑代办" if item else "新建代办")
        title.setStyleSheet("font-size: 16px; font-weight: 600;")
        close_button = QToolButton(self.widget)
        close_button.setIcon(colored_icon("x", Color.TEXT_SECONDARY, 16))
        close_button.setFixedSize(24, 24)
        close_button.setStyleSheet(
            "QToolButton { border: none; border-radius: 4px; background: transparent; }"
            f"QToolButton:hover {{ background: {Color.DANGER_LIGHT}; }}"
        )
        close_button.clicked.connect(self.reject)
        title_row.addWidget(title)
        title_row.addStretch(1)
        title_row.addWidget(close_button)
        self.viewLayout.addLayout(title_row)

        # 表单滚动区（§4.3.1：超出最大高度时内部滚动，滚轮可用）
        scroll = DialogScrollArea(self.widget)
        form = QWidget()
        form_layout = QVBoxLayout(form)
        form_layout.setContentsMargins(0, 0, 8, 0)
        form_layout.setSpacing(Space.XS)
        scroll.setWidget(form)
        self.viewLayout.addWidget(scroll, 1)

        # ===== 字段顺序严格按 §4.3.2 =====

        # 1. 代办名称 *
        form_layout.addLayout(self._field_label("代办名称", required=True))
        self.name_edit = LineEdit(self.widget)
        self.name_edit.setPlaceholderText("输入代办名称…")
        self.name_edit.setFixedHeight(40)
        self.name_edit.setStyleSheet(_FIELD_QSS)
        form_layout.addWidget(self.name_edit)
        self.name_error = self._error_label()
        form_layout.addWidget(self.name_error)

        # 2. 重复周期 + 计划日期（并排两列）+ 联动展开区
        form_layout.addLayout(self._build_repeat_area())

        # 3. 延期策略
        form_layout.addLayout(self._build_delay_area())

        # 4. 关联目标（可选，MVP 禁用占位）
        form_layout.addLayout(self._build_goal_area())

        # 5. 描述（可选，超过 3 行自动撑高）
        form_layout.addLayout(self._field_label("描述（可选）"))
        self.desc_edit = AutoGrowTextEdit(min_lines=3, parent=self.widget)
        self.desc_edit.setPlaceholderText("补充细节、背景信息…")
        self.desc_edit.setStyleSheet(_FIELD_QSS)
        form_layout.addWidget(self.desc_edit)

        # 6. 完成标准 *（核心特色，超过 4 行自动撑高）
        form_layout.addLayout(
            self._field_label("完成标准", required=True, hint="💡 明确标准，事后才能高质量复盘")
        )
        self.standard_edit = AutoGrowTextEdit(min_lines=4, parent=self.widget)
        self.standard_edit.setPlaceholderText("做到什么程度算完成？具体、可衡量、可验证…")
        self.standard_edit.setStyleSheet(_FIELD_QSS)
        form_layout.addWidget(self.standard_edit)
        self.standard_error = self._error_label()
        form_layout.addWidget(self.standard_error)

        # 软引导（框内右下角提示，随输入消失）
        self._guide = QLabel(
            "建议：用『输出物』+『标准』描述，\n如『输出读书笔记 3 条，能复述作者核心观点』",
            self.standard_edit,
        )
        self._guide.setStyleSheet(
            f"color: {Color.TEXT_TERTIARY}; font-size: {FontSize.TINY}px; background: transparent;"
        )
        self._guide.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._guide.adjustSize()
        self.standard_edit.textChanged.connect(self._update_guide)

        form_layout.addStretch(1)

        # 按钮
        self.yesButton.setText("保存修改" if item else "创建代办")
        self.cancelButton.setText("取消")

        if item:
            self.name_edit.setText(item.name)
            self.desc_edit.setPlainText(item.description or "")
            self.standard_edit.setPlainText(item.standard or "")
            self._prefill_repeat(item)
            if item.delay_policy in self.delay_buttons:
                self.delay_buttons[item.delay_policy].setChecked(True)
        self._update_guide()

    # ---------- 外观 ----------
    def _unify_background(self) -> None:
        """弹窗内部统一纯白（--surface）：覆盖 fluent 默认的灰色底部按钮栏。"""
        self.setStyleSheet(
            self.styleSheet()
            + f"#buttonGroup {{ background: {Color.SURFACE};"
            + f" border-top: 1px solid {Color.BG_SECONDARY};"
            + " border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; }"
        )

    # ---------- 重复周期 + 日期联动 ----------
    def _build_repeat_area(self) -> QVBoxLayout:
        area = QVBoxLayout()
        area.setContentsMargins(0, 0, 0, 0)
        area.setSpacing(Space.XS)

        row = QHBoxLayout()
        row.setSpacing(Space.MD)

        col_repeat = QVBoxLayout()
        col_repeat.setSpacing(Space.XS)
        col_repeat.addWidget(self._plain_label("重复周期"))
        self.repeat_combo = ChevronComboBox(self.widget)
        for value in (REPEAT_NONE, REPEAT_DAILY, REPEAT_WEEKLY, REPEAT_MONTHLY):
            self.repeat_combo.addItem(REPEAT_LABELS[value], value)
        self.repeat_combo.setFixedHeight(40)
        self.repeat_combo.setStyleSheet(_FIELD_QSS)
        col_repeat.addWidget(self.repeat_combo)
        row.addLayout(col_repeat, 1)

        # 日期区：不重复 → 单个计划日期；每日/每周/每月 → 开始 + 结束（均必填）
        self.date_stack = QStackedWidget(self.widget)
        self.date_stack.addWidget(self._page_none())  # 0：计划日期
        self.date_stack.addWidget(self._page_range())  # 1：开始日期 + 结束日期
        row.addWidget(self.date_stack, 2)

        area.addLayout(row)

        # 编辑重复系列单条记录时的只读提示（默认隐藏）
        self.repeat_hint = QLabel("重复代办的修改仅作用于当前这一条")
        self.repeat_hint.setStyleSheet(
            f"color: {Color.TEXT_TERTIARY}; font-size: {FontSize.TINY}px;"
        )
        self.repeat_hint.hide()
        area.addWidget(self.repeat_hint)

        # 生成条数实时预览 / 校验错误提示（默认隐藏）
        self.preview_label = QLabel("")
        self.preview_label.hide()
        area.addWidget(self.preview_label)

        # 信号：重复切换与日期变化都刷新预览
        self.repeat_combo.currentIndexChanged.connect(self._on_repeat_changed)
        self.start_picker.dateChanged.connect(lambda _v: self._update_preview())
        self.end_picker.dateChanged.connect(lambda _v: self._update_preview())
        self.end_picker.dateCleared.connect(self._update_preview)
        return area

    def _page_none(self) -> QWidget:
        page = QWidget(self.widget)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Space.XS)
        layout.addWidget(self._plain_label("计划日期"))
        self.date_picker = DatePickerButton(page)
        self.date_picker.setDate(QDate.currentDate())
        layout.addWidget(self.date_picker)
        return page

    def _page_range(self) -> QWidget:
        """每日/每周/每月：开始日期 + 结束日期（均必填）。

        每周的“周几”由开始日期隐含决定；每月的“几号”由开始日期的日号隐含决定，
        不再有星期多选 / 1~31 网格（UI v1.3）。
        """
        page = QWidget(self.widget)
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Space.MD)

        col_start = QVBoxLayout()
        col_start.setSpacing(Space.XS)
        col_start.addWidget(self._plain_label("开始日期", required=True))
        self.start_picker = DatePickerButton(page)
        self.start_picker.setDate(QDate.currentDate())
        col_start.addWidget(self.start_picker)
        layout.addLayout(col_start, 1)

        col_end = QVBoxLayout()
        col_end.setSpacing(Space.XS)
        col_end.addWidget(self._plain_label("结束日期", required=True))
        self.end_picker = DatePickerButton(page, placeholder="选择结束日期")
        col_end.addWidget(self.end_picker)
        layout.addLayout(col_end, 1)
        return page

    def _on_repeat_changed(self, _index: int) -> None:
        repeat = self.repeat_combo.currentData()
        self.date_stack.setCurrentIndex(0 if repeat == REPEAT_NONE else 1)
        self._update_preview()

    # ---------- 生成条数预览与校验 ----------
    @staticmethod
    def _to_pydate(qdate: QDate) -> date:
        return date(qdate.year(), qdate.month(), qdate.day())

    def _repeat_error(self) -> str | None:
        """重复日期区间校验：合法返回 None，否则返回错误文案。"""
        if not self.end_picker.hasDate():
            return "请选择结束日期"
        start = self._to_pydate(self.start_picker.getDate())
        end = self._to_pydate(self.end_picker.getDate())
        try:
            expand_dates(self.repeat_combo.currentData(), start, end)
        except ValueError as e:
            return str(e)
        return None

    def _update_preview(self) -> None:
        """实时预览“将生成 N 条代办”；校验失败红色提示并禁用确认按钮。"""
        if self._editing_repeat or self.repeat_combo.currentData() == REPEAT_NONE:
            self.preview_label.hide()
            self.yesButton.setEnabled(True)
            return
        error = self._repeat_error()
        if error is not None:
            self.preview_label.setText(error)
            self.preview_label.setStyleSheet(
                f"color: {Color.DANGER}; font-size: {FontSize.TINY}px;"
            )
            self.preview_label.show()
            self.yesButton.setEnabled(False)
            return
        dates = expand_dates(
            self.repeat_combo.currentData(),
            self._to_pydate(self.start_picker.getDate()),
            self._to_pydate(self.end_picker.getDate()),
        )
        self.preview_label.setText(
            f"将生成 {len(dates)} 条代办（首条 {dates[0].isoformat()}，"
            f"末条 {dates[-1].isoformat()}）"
        )
        self.preview_label.setStyleSheet(
            f"color: {Color.TEXT_TERTIARY}; font-size: {FontSize.TINY}px;"
        )
        self.preview_label.show()
        self.yesButton.setEnabled(True)

    def expanded_count(self) -> int | None:
        """创建重复代办时将生成的记录条数（供成功反馈文案）；不重复/非法区间返回 None。"""
        if self._editing_repeat or self.repeat_combo.currentData() == REPEAT_NONE:
            return None
        if self._repeat_error() is not None:
            return None
        return len(
            expand_dates(
                self.repeat_combo.currentData(),
                self._to_pydate(self.start_picker.getDate()),
                self._to_pydate(self.end_picker.getDate()),
            )
        )

    def _prefill_repeat(self, item: TodoItem) -> None:
        index = self.repeat_combo.findData(item.repeat)
        self.repeat_combo.setCurrentIndex(index)
        if item.date:
            self.date_picker.setDate(QDate(item.date.year, item.date.month, item.date.day))
        if item.repeat != REPEAT_NONE:
            # 重复系列中的单条记录：重复/日期区只读，编辑仅作用于当前这一条
            self.date_stack.setCurrentIndex(0)
            self.repeat_combo.setEnabled(False)
            self.date_stack.setEnabled(False)
            self.repeat_hint.show()
            self.preview_label.hide()
            self.yesButton.setEnabled(True)

    # ---------- 延期策略（T12，§4.3.3 圆形单选组） ----------
    def _build_delay_area(self) -> QVBoxLayout:
        area = QVBoxLayout()
        area.setContentsMargins(0, 0, 0, 0)
        area.setSpacing(Space.XS)

        area.addLayout(self._field_label("延期策略"))

        row = QHBoxLayout()
        row.setSpacing(Space.LG)
        self.delay_group = QButtonGroup(self.widget)
        self.delay_group.setExclusive(True)
        self.delay_buttons: dict[str, QRadioButton] = {}
        for i, (value, label) in enumerate(
            (("default", "默认（不延期）"), ("never", "不延期"), ("auto", "自动延期"))
        ):
            radio = QRadioButton(label, self.widget)
            radio.setStyleSheet(_RADIO_QSS)
            radio.setProperty("delay_value", value)
            self.delay_group.addButton(radio, i)
            row.addWidget(radio)
            self.delay_buttons[value] = radio
        self.delay_buttons["default"].setChecked(True)
        row.addStretch(1)
        area.addLayout(row)

        hint = QLabel("自动延期：过期未完成将顺延至次日")
        hint.setStyleSheet(f"color: {Color.TEXT_TERTIARY}; font-size: {FontSize.TINY}px;")
        area.addWidget(hint)
        return area

    def _selected_delay_policy(self) -> str:
        for value, radio in self.delay_buttons.items():
            if radio.isChecked():
                return value
        return "default"

    # ---------- 关联目标（T12，MVP 禁用占位） ----------
    def _build_goal_area(self) -> QVBoxLayout:
        area = QVBoxLayout()
        area.setContentsMargins(0, 0, 0, 0)
        area.setSpacing(Space.XS)

        area.addLayout(self._field_label("关联目标（可选）"))

        self.goal_edit = LineEdit(self.widget)
        self.goal_edit.setPlaceholderText("目标模块上线后可关联")
        self.goal_edit.setFixedHeight(40)
        self.goal_edit.setEnabled(False)
        self.goal_edit.setStyleSheet(_FIELD_QSS)
        area.addWidget(self.goal_edit)

        hint = QLabel("MVP 暂未启用（目标计划属 v1.0）")
        hint.setStyleSheet(f"color: {Color.TEXT_TERTIARY}; font-size: {FontSize.TINY}px;")
        area.addWidget(hint)
        return area

    # ---------- 表单部件 ----------
    def _plain_label(self, text: str, required: bool = False) -> QLabel:
        label = QLabel(f'{text} <span style="color:{Color.DANGER}">*</span>' if required else text)
        label.setStyleSheet(f"font-size: {FontSize.BODY}px; font-weight: 500;")
        return label

    def _field_label(self, text: str, required: bool = False, hint: str = "") -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, Space.SM, 0, 0)
        label = QLabel(f'{text} <span style="color:{Color.DANGER}">*</span>' if required else text)
        label.setStyleSheet(f"font-size: {FontSize.BODY}px; font-weight: 500;")
        row.addWidget(label)
        if hint:
            hint_label = QLabel(hint)
            hint_label.setStyleSheet(f"color: {Color.TEXT_TERTIARY}; font-size: {FontSize.TINY}px;")
            row.addStretch(1)
            row.addWidget(hint_label)
        else:
            row.addStretch(1)
        return row

    def _error_label(self) -> QLabel:
        label = QLabel("")
        label.setStyleSheet(f"color: {Color.DANGER}; font-size: {FontSize.AUXILIARY}px;")
        label.hide()
        return label

    def _update_guide(self) -> None:
        has_text = bool(self.standard_edit.toPlainText().strip())
        self._guide.setVisible(not has_text)
        if not has_text:
            self._guide.move(16, self.standard_edit.height() - self._guide.height() - 10)

    # ---------- 校验 ----------
    def validate(self) -> bool:
        ok = True
        if not self.name_edit.text().strip():
            self._mark_error(self.name_edit, self.name_error, "请输入代办名称")
            ok = False
        else:
            self._clear_error(self.name_edit, self.name_error)

        if not self.standard_edit.toPlainText().strip():
            self._mark_error(self.standard_edit, self.standard_error, "请填写完成标准")
            ok = False
        else:
            self._clear_error(self.standard_edit, self.standard_error)

        # 重复日期区间兑底校验（正常已被预览提示 + 禁用确认按钮拦截）
        if (
            not self._editing_repeat
            and self.repeat_combo.currentData() != REPEAT_NONE
            and self._repeat_error() is not None
        ):
            ok = False

        if not ok:
            self._shake()
        return ok

    def _mark_error(self, field: QWidget, label: QLabel, message: str) -> None:
        field.setStyleSheet(_ERROR_QSS)
        label.setText(message)
        label.show()
        field.setFocus()

    def _clear_error(self, field: QWidget, label: QLabel) -> None:
        field.setStyleSheet(_FIELD_QSS)
        label.hide()

    def _shake(self) -> None:
        pos = self.widget.pos()
        anim = QPropertyAnimation(self.widget, b"pos", self)
        anim.setDuration(200)
        anim.setKeyValues(
            [
                (0.0, pos),
                (0.25, pos + type(pos)(-8, 0)),
                (0.5, pos + type(pos)(8, 0)),
                (0.75, pos + type(pos)(-4, 0)),
                (1.0, pos),
            ]
        )
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._shake_anim = anim

    # ---------- 数据 ----------
    def get_data(self) -> dict:
        data: dict = {
            "name": self.name_edit.text().strip(),
            "description": self.desc_edit.toPlainText().strip(),
            "standard": self.standard_edit.toPlainText().strip(),
            "delay_policy": self._selected_delay_policy(),
        }
        if self._editing_repeat:
            # 重复系列单条记录：重复/日期字段锁定，不下发（编辑仅作用于当前这一条）
            return data

        repeat = self.repeat_combo.currentData()
        data["repeat"] = repeat
        if repeat == REPEAT_NONE:
            data["day"] = self._to_pydate(self.date_picker.getDate())
        else:
            # 每日/每周/每月：开始日期 + 结束日期，创建时一次性展开（T19/T24）
            data["day"] = self._to_pydate(self.start_picker.getDate())
            data["end_date"] = self._to_pydate(self.end_picker.getDate())
        return data

    def edit_item_id(self) -> int | None:
        return self._item.id if self._item else None
