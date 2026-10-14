"""TaskCard 组件测试（T06）。"""

from datetime import date, datetime, timedelta

from shiguang.services.dto import STATUS_ARCHIVED, TodoItem
from shiguang.ui.widgets.task_card import TaskCard


def _item(**kwargs) -> TodoItem:
    kwargs.setdefault("id", 1)
    kwargs.setdefault("name", "测试代办")
    kwargs.setdefault("standard", "完成标准")
    return TodoItem(**kwargs)


def test_pending_card(qtbot):
    card = TaskCard()
    qtbot.addWidget(card)
    card.set_data(_item(date=date.today()))
    assert card.name_label._full_text == "测试代办"
    assert not card.checkbox.is_checked()


def test_checkbox_click_emits_archive(qtbot):
    card = TaskCard()
    qtbot.addWidget(card)
    card.set_data(_item(date=date.today()))
    fired = []
    card.archive_requested.connect(fired.append)
    card.checkbox.clicked.emit()
    assert fired == [1]


def test_archived_card_readonly(qtbot):
    card = TaskCard()
    qtbot.addWidget(card)
    card.set_data(
        _item(
            status=STATUS_ARCHIVED,
            score=4,
            duration=30,
            archived_at=datetime.now(),
        )
    )
    assert card.checkbox.is_checked()  # 只读绿色勾选
    assert card.menu_button.isHidden()


def test_overdue_style(qtbot):
    card = TaskCard()
    qtbot.addWidget(card)
    card.set_data(_item(date=date.today() - timedelta(days=1), delay_policy="auto", delay_count=1))
    assert Color_DANGER_in(card.styleSheet())


def Color_DANGER_in(stylesheet: str) -> bool:
    from shiguang.ui.theme import Color

    return Color.DANGER in stylesheet
