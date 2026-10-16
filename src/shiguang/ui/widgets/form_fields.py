"""表单基础控件（UI 设计文档 §5.6 + §9.3.2 图标规则）。

- `NumberField`：数字输入框。替代 Qt 原生 SpinBox——原生上下步进箭头（^ v）
  属于系统绘制的子控件，点击区域小、精度差，违反图标规则（AGENT.md「UI 样式规则」）。
  这里改为纯文本输入 + 右侧内嵌 Feather 时钟矢量图标；获得焦点时支持鼠标滚轮微调。
- `ChevronComboBox`：下拉框。隐藏 Qt 原生 down-arrow，改用 Feather
  chevron-down 矢量图标覆盖层。
- `AutoGrowTextEdit`：多行输入框。内容超过默认行数时自动撑高，不出现内部滚动条
  （设置 max_lines 时超过上限才回退内部滚动，如归档总结框 §4.4.3：4～8 行）。
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget
from qfluentwidgets import LineEdit, TextEdit

from shiguang.ui.icons import colored_pixmap
from shiguang.ui.theme import Color, FontSize

_FIELD_QSS = f"""
LineEdit {{
    background: {Color.SURFACE};
    border: 1px solid {Color.BG_SECONDARY};
    border-radius: 8px;
    padding: 8px 36px 8px 12px;
    font-size: {FontSize.BODY}px;
}}
LineEdit:focus {{
    border: 1px solid {Color.PRIMARY};
}}
"""

_COMBO_ARROW_QSS = """
QComboBox::drop-down {
    border: none;
    width: 0px;
}
QComboBox::down-arrow {
    image: none;
    width: 0px;
}
QComboBox {
    padding-right: 32px;
}
"""


class NumberField(QWidget):
    """数字输入框（无原生步进箭头，焦点下滚轮 ±1）。

    对外 API 对齐 QSpinBox 的常用子集：value() / setValue() / valueChanged。
    """

    valueChanged = Signal(int)

    def __init__(
        self,
        value: int = 30,
        minimum: int = 1,
        maximum: int = 100000,
        height: int = 44,
        icon: str = "clock",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._min = minimum
        self._max = maximum

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.edit = LineEdit(self)
        self.edit.setValidator(QIntValidator(minimum, maximum, self))
        self.edit.setText(str(value))
        self.edit.setFixedHeight(height)
        self.edit.setStyleSheet(_FIELD_QSS)
        layout.addWidget(self.edit)

        # 右侧内嵌 Feather 矢量图标（装饰，鼠标事件穿透）
        self._icon = QLabel(self.edit)
        self._icon.setPixmap(colored_pixmap(icon, Color.TEXT_TERTIARY, 16))
        self._icon.setFixedSize(16, 16)
        self._icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._icon.show()

        self.edit.textChanged.connect(self._on_text_changed)

    # ---------- QSpinBox 兼容 API ----------
    def value(self) -> int:
        """当前值；空文本或非法输入按 0 处理（用于必填校验）。"""
        text = self.edit.text().strip()
        if not text or not text.lstrip("-").isdigit():
            return 0
        return max(self._min, min(self._max, int(text)))

    def setValue(self, value: int) -> None:
        self.edit.setText(str(max(self._min, min(self._max, value))))

    # ---------- 交互 ----------
    def wheelEvent(self, event) -> None:
        """仅当输入框持有焦点时滚轮微调，否则交给父级滚动区，避免劫持页面滚动。"""
        if self.edit.hasFocus():
            step = 1 if event.angleDelta().y() > 0 else -1
            self.setValue(self.value() + step)
            event.accept()
        else:
            event.ignore()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._icon.move(self.edit.width() - 16 - 12, (self.edit.height() - 16) // 2)

    def _on_text_changed(self, text: str) -> None:
        self.valueChanged.emit(self.value())


class ChevronComboBox(QComboBox):
    """下拉框：隐藏 Qt 原生 down-arrow，改用 Feather chevron-down 矢量图标。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._arrow = QLabel(self)
        self._arrow.setPixmap(colored_pixmap("chevron-down", Color.TEXT_TERTIARY, 14))
        self._arrow.setFixedSize(14, 14)
        self._arrow.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._arrow.show()

    @staticmethod
    def arrow_qss() -> str:
        """隐藏原生下拉箭头的 QSS 片段（并入调用方的下拉框样式表）。"""
        return _COMBO_ARROW_QSS

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._arrow.move(self.width() - 14 - 12, (self.height() - 14) // 2)


class AutoGrowTextEdit(TextEdit):
    """随内容自动增高的多行输入框。

    内容超过 min_lines 时自动撑高（不出现内部滚动条）；
    传入 max_lines 时超过上限才回退为内部滚动（如归档总结框 §4.4.3：最小 4 行、最大 8 行）。
    超高内容由所在对话框的 QScrollArea 承接滚动。
    """

    def __init__(
        self, min_lines: int = 3, max_lines: int | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        # 隐藏 qfluentwidgets 的 EditLayer 焦点条：它是直角矩形子控件，绘制在控件底部
        # 且越过圆角边框，呈现为底边下一排断点状色块（失焦即消失，截图时看不到）
        self.layer.hide()
        self._min_lines = min_lines
        self._max_lines = max_lines
        if max_lines is None:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.textChanged.connect(self._sync_height)
        self._sync_height()

    def _height_for(self, lines: int) -> int:
        """按行数换算像素高度（含文档边距、上下 padding 8px、1px 边框与余量）。"""
        line_h = self.fontMetrics().lineSpacing()
        doc_margin = self.document().documentMargin()
        return int(lines * line_h + doc_margin * 2 + 8 * 2 + 2 + 4)

    def _visual_lines(self) -> int:
        """可见行数（含自动换行）。需先强制布局，否则未显示时 lineCount 不准。"""
        doc = self.document()
        doc.documentLayout().documentSize()  # 强制完成排版
        lines = 0
        block = doc.begin()
        while block.isValid():
            lines += max(1, block.layout().lineCount())
            block = block.next()
        return max(1, lines)

    def _sync_height(self) -> None:
        height = self._height_for(max(self._min_lines, self._visual_lines()))
        if self._max_lines is not None:
            height = min(height, self._height_for(self._max_lines))
        self.setFixedHeight(height)

    def resizeEvent(self, event) -> None:
        # 宽度确定/变化后换行数会变，重新计算高度
        super().resizeEvent(event)
        self._sync_height()
