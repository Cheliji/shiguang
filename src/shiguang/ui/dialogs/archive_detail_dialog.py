"""归档详情弹窗（只读）。"""

from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
from qfluentwidgets import MessageBoxBase

from shiguang.services.dto import TodoItem
from shiguang.ui.theme import Color, FontSize, Radius, Space, set_container_bg
from shiguang.ui.widgets.rating_widget import RatingWidget


class ArchiveDetailDialog(MessageBoxBase):
    """查看归档记录详情（§4.2.4：名称、归档时间、用时、星级、总结）。"""

    def __init__(self, parent: QWidget | None = None, item: TodoItem | None = None) -> None:
        super().__init__(parent)
        self.widget.setFixedWidth(480)
        self.yesButton.setText("关闭")
        self.cancelButton.hide()

        title = QLabel("归档详情")
        title.setStyleSheet("font-size: 16px; font-weight: 600;")
        self.viewLayout.addWidget(title)

        if item:
            name = QLabel(item.name)
            name.setStyleSheet("font-size: 15px; font-weight: 500;")
            self.viewLayout.addWidget(name)

            time_text = item.archived_at.strftime("%Y-%m-%d %H:%M") if item.archived_at else ""
            time_label = QLabel(f"归档时间：{time_text}")
            time_label.setStyleSheet(
                f"color: {Color.TEXT_SECONDARY}; font-size: {FontSize.AUXILIARY}px;"
            )
            self.viewLayout.addWidget(time_label)

            row = QHBoxLayout()
            row.setSpacing(Space.LG)
            stars = RatingWidget(size=20, read_only=True)
            stars.set_score(item.score or 0)
            row.addWidget(stars)
            duration = QLabel(f"用时 {item.duration or 0} 分钟")
            duration.setStyleSheet(
                f"color: {Color.TEXT_SECONDARY}; font-size: {FontSize.AUXILIARY}px;"
            )
            row.addWidget(duration)
            row.addStretch(1)
            self.viewLayout.addLayout(row)

            summary_box = QWidget(self.widget)
            set_container_bg(summary_box, "archiveSummaryBox", Color.BG_PRIMARY, Radius.MD)
            summary_layout = QVBoxLayout(summary_box)
            summary_layout.setContentsMargins(Space.MD, Space.MD, Space.MD, Space.MD)
            summary = QLabel(item.summary or "（无总结）")
            summary.setWordWrap(True)
            summary.setStyleSheet(f"color: {Color.TEXT_PRIMARY}; font-size: {FontSize.BODY}px;")
            summary_layout.addWidget(summary)
            self.viewLayout.addWidget(summary_box)
