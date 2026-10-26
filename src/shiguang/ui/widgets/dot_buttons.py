"""矢量圆点选择控件（QPainter 自绘，规避 QSS 圆角失效/缩放残留问题）。

QSS 的 border-radius 在动态改尺寸时容易出现方角与旧图残留，且圆角非正圆；
这里改为 QPainter 抗锯齿矢量绘制：画布尺寸固定，选中态通过「圆点放大 +
主题色光环」表达，不触发任何 widget 尺寸变化。
"""

from PySide6.QtCore import QPointF, QRect, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QAbstractButton, QSizePolicy, QWidget

from shiguang.ui.theme import Color


class DotRadioButton(QAbstractButton):
    """圆形单选按钮：圆环 + 选中实心点的矢量绘制版本（替代 QRadioButton）。

    - 未选中：Gray-300 圆环；悬停/选中：主色圆环
    - 选中：圆环内填充主色实心点
    - 可加入 QButtonGroup 实现互斥，行为与 QRadioButton 一致
    """

    INDICATOR = 20  # 圆环外径
    SPACING = 6  # 圆环与文字间距
    RING = 2  # 圆环线宽
    DOT = 10  # 选中内点直径

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setText(text)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # 背景完全由 paintEvent 绘制，禁止样式擦除默认背景（否则会画出方形底色）
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._hovered = False

    # ---------- 悬停跟踪 ----------
    def enterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    # ---------- 尺寸 ----------
    def sizeHint(self) -> QSize:
        fm = self.fontMetrics()
        width = self.INDICATOR + self.SPACING + fm.horizontalAdvance(self.text()) + 4
        height = max(self.INDICATOR, fm.height()) + 6
        return QSize(width, height)

    # ---------- 绘制 ----------
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        checked = self.isChecked()
        center = QPointF(self.INDICATOR / 2 + 1, self.height() / 2)

        # 选中内点
        painter.setPen(Qt.PenStyle.NoPen)
        if checked:
            painter.setBrush(QColor(Color.PRIMARY))
            painter.drawEllipse(center, self.DOT / 2, self.DOT / 2)

        # 圆环（悬停或选中时变主题色）
        ring_color = Color.PRIMARY if (self._hovered or checked) else Color.BG_TERTIARY
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(ring_color), self.RING))
        ring_radius = (self.INDICATOR - self.RING) / 2
        painter.drawEllipse(center, ring_radius, ring_radius)

        # 文字
        painter.setPen(QColor(Color.TEXT_PRIMARY))
        text_rect = QRect(
            self.INDICATOR + self.SPACING, 0,
            self.width() - self.INDICATOR - self.SPACING, self.height(),
        )
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self.text(),
        )

        # 键盘焦点提示
        if self.hasFocus():
            painter.setPen(QPen(QColor(Color.PRIMARY_SUBTLE), 1))
            painter.drawRoundedRect(self.rect().adjusted(0, 2, -1, -2), 6, 6)

        painter.end()


class PriorityDotButton(QAbstractButton):
    """重要程度圆点按钮：纯色圆点，选中放大 + 主题色浅光环。

    画布固定（40px），选中只在绘制层放大圆点（28 → 32px），
    不触发 widget 尺寸变化，因此无任何缩放残留。
    """

    CANVAS = 40  # 固定画布（容纳最大圆点 + 光环）
    DOT = 28  # 未选中圆点直径
    DOT_CHECKED = 32  # 选中圆点直径
    HALO_GAP = 1  # 圆点与光环间距

    def __init__(self, color_hex: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = QColor(color_hex)
        self.setCheckable(True)
        self.setFixedSize(self.CANVAS, self.CANVAS)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # 背景完全由 paintEvent 绘制，禁止样式擦除默认背景（否则会画出方形底色）
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._hovered = False

    # ---------- 悬停跟踪 ----------
    def enterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    # ---------- 绘制 ----------
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        checked = self.isChecked()
        center = QPointF(self.width() / 2, self.height() / 2)
        dot_d = self.DOT_CHECKED if checked else self.DOT
        dot_radius = dot_d / 2

        # 光环：选中 3px、悬停 2px 主题色浅环（1px 间隙，描边圆实现）
        if checked or self._hovered:
            halo_width = 3 if checked else 2
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(Color.PRIMARY_SUBTLE), halo_width))
            halo_radius = dot_radius + self.HALO_GAP + halo_width / 2
            painter.drawEllipse(center, halo_radius, halo_radius)

        # 圆点（按下时略加深）
        color = self._color.darker(105) if self.isDown() else self._color
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(center, dot_radius, dot_radius)

        painter.end()
