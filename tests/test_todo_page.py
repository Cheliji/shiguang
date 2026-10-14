"""TodoPage 测试（T14）。"""

from datetime import date, timedelta

import pytest
from PySide6.QtWidgets import QMainWindow

from shiguang.services.mock.mock_task_service import MockTaskService
from shiguang.ui.pages.todo_page import TodoPage


@pytest.fixture()
def window(qtbot):
    win = QMainWindow()
    win.resize(1100, 720)
    qtbot.addWidget(win)
    return win


def _make_page(qtbot, service):
    import shiguang.ui.pages.todo_page as module

    original = module.get_task_service
    module.get_task_service = lambda: service
    try:
        page = TodoPage()
    finally:
        module.get_task_service = original
    qtbot.addWidget(page)
    return page


def test_tab_switch_counts(qtbot, window):
    service = MockTaskService(with_seed=True)
    page = _make_page(qtbot, service)

    page._on_tab_changed(2)  # 逾期
    assert page._current_tab == 2
    overdue_count = len(service.list_overdue())
    cards = page.list_layout.count()
    assert cards == overdue_count

    page._on_tab_changed(3)  # 已归档
    archived_count = len(service.list_archived())
    assert page.list_layout.count() == archived_count


def test_date_filter_recent7(qtbot, window):
    service = MockTaskService(with_seed=False)
    today = date.today()
    service.create_todo(name="今天", standard="s", day=today)
    service.create_todo(name="十天前", standard="s", day=today - timedelta(days=10))
    page = _make_page(qtbot, service)

    page._on_tab_changed(1)  # 待办
    page.date_filter.setCurrentIndex(2)  # 最近7天
    assert page.list_layout.count() >= 1  # 今天在范围内（含日期分组头）
    # 切到全部日期
    page.date_filter.setCurrentIndex(0)
    page.refresh()


def test_empty_state_archived(qtbot, window):
    service = MockTaskService(with_seed=False)
    page = _make_page(qtbot, service)
    page._on_tab_changed(3)  # 已归档，无数据
    # 空状态 holder 一个 widget
    assert page.list_layout.count() == 1
