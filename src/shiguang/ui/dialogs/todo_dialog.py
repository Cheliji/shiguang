"""代办创建/编辑对话框（规格：UI 设计文档 §4.3）。

T10 范围：名称（必填）/ 描述（可选）/ 完成标准（必填）+ 校验交互（§6.2 红框 + 抖动）。
重复/日期联动属 T11，延期/目标属 T12——布局已预留位置（表单自上而下追加）。
"""

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolButton, QWidget
from qfluentwidgets import LineEdit, MessageBoxBase, TextEdit

from shiguang.services.dto import TodoItem
from shiguang.ui.icons import colored_icon
from shiguang.ui.theme import Color, FontSize, Space

_FIELD_QSS = f"""
LineEdit, TextEdit {{
    background: {Color.SURFACE};
    border: 1px solid {Color.BG_SECONDARY};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: {FontSize.BODY}px;
}}
LineEdit:focus, TextEdit:focus {{
    border: 1px solid {Color.PRIMARY};
}}
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


class TodoDialog(MessageBoxBase):
    """创建/编辑代办对话框。

    mode: "create" / "edit"；edit 模式传入 item 预填。
    校验通过后 accept()，调用方通过 get_data() 取表单数据。
    """

    def __init__(self, parent: QWidget | None = None, item: TodoItem | None = None) -> None:
        super().__init__(parent)
        self._item = item
        self.widget.setFixedWidth(520)

        # 标题行：标题 + 关闭按钮（§4.3.3）
        title_row = QHBoxLayout()
        title = QLabel("编辑代办" if item else "新建代办")
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

        # 代办名称 *
        self.viewLayout.addLayout(self._field_label("代办名称", required=True))
        self.name_edit = LineEdit(self.widget)
        self.name_edit.setPlaceholderText("输入代办名称…")
        self.name_edit.setFixedHeight(40)
        self.name_edit.setStyleSheet(_FIELD_QSS)
        self.viewLayout.addWidget(self.name_edit)
        self.name_error = self._error_label()
        self.viewLayout.addWidget(self.name_error)

        # 描述（可选）
        self.viewLayout.addLayout(self._field_label("描述（可选）"))
        self.desc_edit = TextEdit(self.widget)
        self.desc_edit.setPlaceholderText("补充细节、背景信息…")
        self.desc_edit.setFixedHeight(80)
        self.desc_edit.setStyleSheet(_FIELD_QSS)
        self.viewLayout.addWidget(self.desc_edit)

        # 完成标准 *（核心特色，§4.3.3：提示 + 软引导）
        self.viewLayout.addLayout(
            self._field_label("完成标准", required=True, hint="💡 明确标准，事后才能高质量复盘")
        )
        self.standard_edit = TextEdit(self.widget)
        self.standard_edit.setPlaceholderText("做到什么程度算完成？具体、可衡量、可验证…")
        self.standard_edit.setFixedHeight(100)
        self.standard_edit.setStyleSheet(_FIELD_QSS)
        self.viewLayout.addWidget(self.standard_edit)
        self.standard_error = self._error_label()
        self.viewLayout.addWidget(self.standard_error)

        # 软引导（输入后消失）
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

        # 日期占位（T11 替换为完整重复/日期联动区）
        date_label = QLabel("📅 计划日期：今天")
        date_label.setStyleSheet(
            f"color: {Color.TEXT_SECONDARY}; font-size: {FontSize.AUXILIARY}px;"
        )
        self.viewLayout.addWidget(date_label)

        # 按钮（§4.3.3：编辑模式文案为"保存修改"）
        self.yesButton.setText("保存修改" if item else "创建代办")
        self.cancelButton.setText("取消")

        if item:
            self.name_edit.setText(item.name)
            self.desc_edit.setPlainText(item.description or "")
            self.standard_edit.setPlainText(item.standard or "")
        self._update_guide()

    # ---------- 表单部件 ----------
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
            edit_height = self.standard_edit.height()
            self._guide.move(16, edit_height - self._guide.height() - 10)

    # ---------- 校验（§6.2：红框 + 错误文案 + 抖动 + 聚焦） ----------
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
        """抖动动画（200ms）。"""
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
        return {
            "name": self.name_edit.text().strip(),
            "description": self.desc_edit.toPlainText().strip(),
            "standard": self.standard_edit.toPlainText().strip(),
        }

    def edit_item_id(self) -> int | None:
        return self._item.id if self._item else None
