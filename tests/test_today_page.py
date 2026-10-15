"""今日首页冒烟测试（T09）。"""

from datetime import date, timedelta

from shiguang.services.mock.mock_task_service import MockTaskService
from shiguang.ui.pages.today_page import TodayPage, mood_emoji


def _make_page(qtbot, service):
    page = TodayPage.__new__(TodayPage)
    # 用指定 service 实例化：临时替换工厂
    import shiguang.ui.pages.today_page as module

    original = module.get_task_service
    module.get_task_service = lambda: service
    try:
        page.__init__()
    finally:
        module.get_task_service = original
    qtbot.addWidget(page)
    return page


def test_mood_emoji_levels():
    assert mood_emoji(0.0) == "🌱"
    assert mood_emoji(0.2) == "☕"
    assert mood_emoji(0.5) == "🙂"
    assert mood_emoji(0.8) == "😊"
    assert mood_emoji(1.0) == "🎉"


def test_page_renders_seed_data(qtbot):
    service = MockTaskService(with_seed=True)
    page = _make_page(qtbot, service)
    today = date.today()
    expected = (
        len(service.list_today(today))
        + len(service.list_overdue())
        + len(service.list_archived(today))
    )
    assert page.count_badge.text() == str(expected)


def test_page_empty_state(qtbot):
    service = MockTaskService(with_seed=False)
    page = _make_page(qtbot, service)
    assert page.count_badge.text() == "0"


def test_date_switch(qtbot):
    service = MockTaskService(with_seed=False)
    tomorrow = date.today() + timedelta(days=1)
    service.create_todo(name="明日事", standard="s", day=tomorrow)
    page = _make_page(qtbot, service)

    page._on_date_selected(tomorrow)
    assert page.count_badge.text() == "1"
    assert page.list_title.text() != "今日代办"

    page._on_date_selected(date.today())
    assert page.list_title.text() == "今日代办"
    assert page.count_badge.text() == "0"


def test_refresh_on_changed(qtbot):
    service = MockTaskService(with_seed=False)
    page = _make_page(qtbot, service)
    service.create_todo(name="新代办", standard="s", day=date.today())
    assert page.count_badge.text() == "1"
