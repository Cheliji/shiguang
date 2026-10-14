"""组件临时预览页（开发期调试用，不进导航）。

运行方式：SHIGUANG_PREVIEW=1 python -m shiguang.main
用 Mock 假数据平铺 TaskCard 的全部状态变体，便于与原型并排比对。
T08 完成后会追加 RatingWidget 预览；T14 完成后本文件保留但默认不启用。
"""

import os

from PySide6.QtWidgets import QMainWindow, QScrollArea, QVBoxLayout, QWidget


def maybe_show_preview() -> bool:
    """若设置了 SHIGUANG_PREVIEW=1，展示预览窗口并返回 True。"""
    if os.environ.get("SHIGUANG_PREVIEW") != "1":
        return False

    from datetime import date, datetime, timedelta

    from shiguang.services.dto import STATUS_ARCHIVED, TodoItem
    from shiguang.ui.widgets.task_card import TaskCard

    today = date.today()
    variants = [
        ("默认", TodoItem(id=1, name="整理电脑桌面文件", standard="收件箱清空", date=today)),
        (
            "每日重复 + 长文本截断",
            TodoItem(
                id=2,
                name="阅读《设计心理学》第三章关于心智模型的部分并整理读书笔记",
                standard="写 3 条读书笔记，每条不少于 50 字，能向朋友复述作者的核心观点",
                date=today,
                repeat="daily",
            ),
        ),
        (
            "逾期 + 已延期",
            TodoItem(
                id=3,
                name="给手机相册分类",
                standard="相册按年份建文件夹",
                date=today - timedelta(days=1),
                delay_policy="auto",
                delay_count=2,
            ),
        ),
        (
            "已归档",
            TodoItem(
                id=4,
                name="晨跑 5 公里",
                standard="配速低于 6:00",
                date=today,
                status=STATUS_ARCHIVED,
                score=4,
                duration=30,
                summary="状态不错",
                archived_at=datetime.now(),
            ),
        ),
    ]

    window = QMainWindow()
    window.setWindowTitle("组件预览")
    window.resize(720, 720)

    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(24, 24, 24, 24)
    layout.setSpacing(8)
    for _title, item in variants:
        card = TaskCard()
        card.set_data(item)
        layout.addWidget(card)
    layout.addStretch(1)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(container)
    window.setCentralWidget(scroll)
    window.show()
    return True
