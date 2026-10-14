"""TaskCard 代办卡片（规格：UI 设计文档 §5.1）。

结构：Checkbox + 名称 + 完成标准摘要 + 元信息行 + 右侧操作菜单（⋯）。
状态变体（§5.1.3）：默认 / 悬停（阴影加深）/ 逾期（红条+浅红底）/ 已延期 Badge / 归档态。
"""

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMenu,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from shiguang.services.dto import REPEAT_LABELS, STATUS_ARCHIVED, TodoItem
from shiguang.ui.icons import colored_icon
from shiguang.ui.theme import Color, FontSize, Space


class CheckBox(QWidget):
    """自绘复选框（§5.1.2：20px、圆角方形 6px、四态）。

    点击发出 clicked（点击 = 发起归档）；归档态为只读绿色勾选。
    """

    clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hover = False
        self._checked = False
        self._read_only = False

    def set_read_only_done(self) -> None:
        """归档态：绿色填充 + 白色勾选，不可点击。"""
        self._checked = True
        self._read_only = True
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()

    def is_checked(self) -> bool:
        return self._checked

    def mousePressEvent(self, event) -> None:
        if not self._read_only and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def enterEvent(self, event) -> None:
        self._hover = True
        self.update()

    def leaveEvent(self, event) -> None:
        self._hover = False
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(1, 1, 18, 18)

        if self._read_only:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(Color.SUCCESS))
        elif self._checked:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(Color.PRIMARY))
        else:
            border = Color.PRIMARY if self._hover else Color.BG_TERTIARY
            painter.setPen(QPen(QColor(border), 2))
            painter.setBrush(QColor(Color.SURFACE))
        painter.drawRoundedRect(rect, 6, 6)

        if self._checked:
            painter.setPen(QPen(QColor("#FFFFFF"), 2, Qt.PenStyle.SolidLine, Qt.PenStyle.RoundCap))
            painter.drawLine(6, 10, 9, 13)
            painter.drawLine(9, 13, 14, 6)
        painter.end()


class ElideLabel(QLabel):
    """单行省略标签（§5.1.2：完成标准摘要溢出显示省略号）。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._full_text = ""

    def set_full_text(self, text: str) -> None:
        self._full_text = text
        self._elide()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._elide()

    def _elide(self) -> None:
        elided = self.fontMetrics().elidedText(
            self._full_text, Qt.TextElideMode.ElideRight, max(self.width(), 10)
        )
        super().setText(elided)


def _pill(text: str, bg: str, fg: str) -> QLabel:
    """Pill 标签（§5.7）。"""
    label = QLabel(text)
    label.setStyleSheet(
        f"background: {bg}; color: {fg}; border-radius: 9px;"
        f"padding: 2px 10px; font-size: {FontSize.TINY}px;"
    )
    label.setFixedHeight(18)
    return label


class TaskCard(QFrame):
    """代办卡片。"""

    archive_requested = Signal(int)
    edit_requested = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._item: TodoItem | None = None
        self._build_ui()
        self._apply_style(overdue=False)
        self._set_shadow(hover=False)

    # ---------- UI 搭建 ----------
    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(Space.LG, Space.MD, Space.LG, Space.MD)
        layout.setSpacing(Space.MD)

        self.checkbox = CheckBox(self)
        self.checkbox.clicked.connect(self._on_checkbox_clicked)
        layout.addWidget(self.checkbox, 0, Qt.AlignmentFlag.AlignTop)

        content = QVBoxLayout()
        content.setSpacing(Space.XS)

        self.name_label = ElideLabel(self)
        self.name_label.setStyleSheet(f"font-size: {FontSize.CARD_TITLE}px; font-weight: 500;")
        content.addWidget(self.name_label)

        standard_row = QHBoxLayout()
        standard_row.setSpacing(Space.XS)
        icon_label = QLabel(self)
        icon_label.setPixmap(colored_icon("clipboard", Color.TEXT_TERTIARY, 13).pixmap(13, 13))
        icon_label.setFixedSize(13, 13)
        self.standard_label = ElideLabel(self)
        self.standard_label.setStyleSheet(
            f"color: {Color.TEXT_SECONDARY}; font-size: {FontSize.AUXILIARY}px;"
        )
        standard_row.addWidget(icon_label)
        standard_row.addWidget(self.standard_label, 1)
        content.addLayout(standard_row)

        self.meta_row = QHBoxLayout()
        self.meta_row.setSpacing(Space.SM)
        content.addLayout(self.meta_row)

        layout.addLayout(content, 1)

        # 右侧：归档信息（归档态）或操作菜单（待办态）
        self.right_label = QLabel(self)
        self.right_label.setStyleSheet(
            f"color: {Color.TEXT_TERTIARY}; font-size: {FontSize.AUXILIARY}px;"
        )
        self.right_label.hide()
        layout.addWidget(self.right_label, 0, Qt.AlignmentFlag.AlignTop)

        self.menu_button = QToolButton(self)
        self.menu_button.setIcon(colored_icon("more-horizontal", Color.TEXT_SECONDARY, 18))
        self.menu_button.setFixedSize(24, 24)
        self.menu_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_button.setStyleSheet(
            "QToolButton { border: none; border-radius: 4px; }"
            f"QToolButton:hover {{ background: {Color.BG_PRIMARY}; }}"
        )
        self.menu_button.clicked.connect(self._show_menu)
        layout.addWidget(self.menu_button, 0, Qt.AlignmentFlag.AlignTop)

    # ---------- 数据渲染 ----------
    def set_data(self, item: TodoItem) -> None:
        self._item = item
        archived = item.status == STATUS_ARCHIVED
        overdue = item.is_overdue()

        self.name_label.set_full_text(item.name)
        name_style = f"font-size: {FontSize.CARD_TITLE}px; font-weight: 500;"
        if archived:
            name_style += f" color: {Color.TEXT_SECONDARY}; text-decoration: line-through;"
        self.name_label.setStyleSheet(name_style)

        self.standard_label.set_full_text(f"完成标准：{item.standard}" if item.standard else "")

        self._render_meta(item, archived, overdue)

        if archived:
            self.checkbox.set_read_only_done()
            self.menu_button.hide()
            score = item.score or 0
            duration = item.duration or 0
            self.right_label.setText(f"★ {score} · {duration}min")
            self.right_label.show()
        else:
            self.right_label.hide()
            self.menu_button.show()

        self._apply_style(overdue=overdue)

    def _render_meta(self, item: TodoItem, archived: bool, overdue: bool) -> None:
        # 清空旧元信息
        while self.meta_row.count():
            child = self.meta_row.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if item.repeat != "none":
            self.meta_row.addWidget(
                _pill(REPEAT_LABELS[item.repeat], Color.PRIMARY_LIGHT, Color.PRIMARY)
            )

        if overdue:
            self.meta_row.addWidget(_pill("逾期", Color.DANGER_LIGHT, Color.DANGER))
        if item.delay_count > 0:
            self.meta_row.addWidget(_pill(f"已延期 {item.delay_count} 次", "#FEF3C7", "#92400E"))
        if archived:
            self.meta_row.addWidget(_pill("已归档", Color.SUCCESS_LIGHT, "#065F46"))

        date_text = ""
        if item.archived_at:
            date_text = item.archived_at.strftime("%m-%d 归档")
        elif item.date:
            date_text = item.date.strftime("%m-%d")
        if date_text:
            color = Color.DANGER if overdue else Color.TEXT_TERTIARY
            date_label = QLabel(f"📅 {date_text}")
            date_label.setStyleSheet(f"color: {color}; font-size: {FontSize.TINY}px;")
            self.meta_row.addWidget(date_label)

        self.meta_row.addStretch(1)

    # ---------- 样式 ----------
    def _apply_style(self, overdue: bool) -> None:
        if overdue:
            bg = "#FFF5F5"
            border_left = f"border-left: 4px solid {Color.DANGER};"
        else:
            bg = Color.SURFACE
            border_left = "border-left: 4px solid transparent;"
        self.setStyleSheet(f"TaskCard {{ background: {bg}; border-radius: 12px; {border_left} }}")

    def _set_shadow(self, hover: bool) -> None:
        effect = QGraphicsDropShadowEffect(self)
        if hover:
            effect.setBlurRadius(12)
            effect.setOffset(0, 4)
            effect.setColor(QColor(0, 0, 0, 15))
        else:
            effect.setBlurRadius(2)
            effect.setOffset(0, 1)
            effect.setColor(QColor(0, 0, 0, 10))
        self.setGraphicsEffect(effect)

    def enterEvent(self, event) -> None:
        self._set_shadow(hover=True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._set_shadow(hover=False)
        super().leaveEvent(event)

    # ---------- 交互 ----------
    def _on_checkbox_clicked(self) -> None:
        if self._item is not None:
            self.archive_requested.emit(self._item.id)

    def _show_menu(self) -> None:
        if self._item is None:
            return
        menu = QMenu(self)
        archive_action = menu.addAction("归档")
        edit_action = menu.addAction("编辑")
        delete_action = menu.addAction("删除")
        action = menu.exec(self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft()))
        if action is archive_action:
            self.archive_requested.emit(self._item.id)
        elif action is edit_action:
            self.edit_requested.emit(self._item.id)
        elif action is delete_action:
            self.delete_requested.emit(self._item.id)

    def sizeHint(self) -> QSize:
        return QSize(400, 76)
