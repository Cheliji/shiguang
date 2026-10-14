"""RatingWidget 星级评分组件（规格：UI 设计文档 §5.3 / §4.4.3）。

5 颗星自绘（QPainter），hover 预览 + 放大、点击确定 + 回弹，支持只读模式与评分标签。
"""

import math

from PySide6.QtCore import QEasingCurve, QPointF, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from shiguang.ui.theme import Color, FontSize

SCORE_LABELS: dict[int, tuple[str, str]] = {
    1: ("还需努力", Color.DANGER),
    2: ("勉强完成", Color.WARNING),
    3: ("基本达标", Color.TEXT_SECONDARY),
    4: ("完成不错", Color.PRIMARY),
    5: ("完美达成", Color.SUCCESS),
}


def _star_path(cx: float, cy: float, outer: float) -> QPainterPath:
    """以 (cx, cy) 为中心的五角星路径。"""
    inner = outer * 0.45
    path = QPainterPath()
    for i in range(10):
        radius = outer if i % 2 == 0 else inner
        angle = math.radians(-90 + i * 36)
        point = QPointF(cx + radius * math.cos(angle), cy + radius * math.sin(angle))
        if i == 0:
            path.moveTo(point)
        else:
            path.lineTo(point)
    path.closeSubpath()
    return path


class RatingWidget(QWidget):
    """星级评分。

    size: 星星边长（28 归档弹窗 / 20 卡片展示）
    show_label: 选中后是否在下方显示评分标签
    read_only: 只读展示（已归档卡片）
    """

    score_changed = Signal(int)

    def __init__(
        self,
        size: int = 28,
        show_label: bool = False,
        read_only: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._size = size
        self._read_only = read_only
        self._score = 0
        self._hover = 0  # 0 表示无悬停
        self._scale = 1.0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._stars_area = _StarsArea(self)
        layout.addWidget(self._stars_area, 0, Qt.AlignmentFlag.AlignHCenter)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFixedHeight(20)
        self.label.hide()
        layout.addWidget(self.label)

        self._show_label = show_label
        if not read_only:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

    # ---------- 公共接口 ----------
    def score(self) -> int:
        return self._score

    def set_score(self, score: int) -> None:
        self._score = max(0, min(5, score))
        self._stars_area.update()
        self._update_label()

    def set_read_only(self, read_only: bool) -> None:
        self._read_only = read_only
        self.setCursor(
            Qt.CursorShape.ArrowCursor if read_only else Qt.CursorShape.PointingHandCursor
        )

    # ---------- 内部 ----------
    def _display_count(self) -> int:
        return self._hover or self._score

    def _star_at(self, x: float) -> int:
        """x 坐标落在第几颗星（1-5），0 表示不在任何星上。"""
        spacing = self._size + 8
        for i in range(5):
            if i * spacing - 4 <= x <= i * spacing + self._size + 4:
                return i + 1
        return 0

    def _on_hover(self, x: float) -> None:
        if self._read_only:
            return
        self._hover = self._star_at(x)
        self._stars_area.update()

    def _on_leave(self) -> None:
        self._hover = 0
        self._stars_area.update()

    def _on_click(self, x: float) -> None:
        if self._read_only:
            return
        star = self._star_at(x)
        if star:
            self.set_score(star)
            self.score_changed.emit(star)
            self._bounce()

    def _bounce(self) -> None:
        """点击回弹 0.9 → 1.0（§7.4）。"""
        self._anim = QVariantAnimation(self)
        self._anim.setStartValue(0.9)
        self._anim.setEndValue(1.0)
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self._anim.valueChanged.connect(self._set_scale)
        self._anim.start()

    def _set_scale(self, value: float) -> None:
        self._scale = value
        self._stars_area.update()

    def _update_label(self) -> None:
        if not self._show_label:
            return
        if self._score in SCORE_LABELS:
            text, color = SCORE_LABELS[self._score]
            self.label.setText(f"⭐ {text}")
            self.label.setStyleSheet(
                f"color: {color}; font-size: {FontSize.BODY}px; font-weight: 500;"
            )
            self.label.show()
        else:
            self.label.hide()


class _StarsArea(QWidget):
    """星星绘制区（内部组件）。"""

    def __init__(self, owner: RatingWidget) -> None:
        super().__init__(owner)
        self._owner = owner
        size = owner._size
        self.setFixedSize(size * 5 + 8 * 4, size + 8)
        self.setMouseTracking(True)

    def mouseMoveEvent(self, event) -> None:
        self._owner._on_hover(event.position().x())

    def leaveEvent(self, event) -> None:
        self._owner._on_leave()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._owner._on_click(event.position().x())

    def paintEvent(self, event) -> None:
        owner = self._owner
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        size = owner._size
        spacing = size + 8
        filled_count = owner._display_count()
        scale = owner._scale
        hover_active = owner._hover > 0

        for i in range(5):
            outer = (size / 2) * scale
            if hover_active and i < filled_count:
                outer *= 1.1  # 悬停放大（§7.4）
            cx = i * spacing + size / 2
            cy = self.height() / 2
            path = _star_path(cx, cy, outer)

            if i < filled_count:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(Color.STAR))
            else:
                painter.setPen(QPen(QColor(Color.STAR_EMPTY), 1.5))
                painter.setBrush(QColor(Color.STAR_EMPTY))
            painter.drawPath(path)

        painter.end()
