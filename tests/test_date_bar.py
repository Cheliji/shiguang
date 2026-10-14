"""DateBar 组件测试（T07）。"""

from datetime import date, timedelta

from shiguang.ui.widgets.date_bar import DateBar, week_dates


def test_week_dates_monday_start():
    # 2026-10-14 是周三（weekday=2）
    days = week_dates(date(2026, 10, 14))
    assert days[0] == date(2026, 10, 12)  # 周一
    assert days[-1] == date(2026, 10, 18)  # 周日
    assert len(days) == 7


def test_week_dates_cross_month():
    # 2026-02-01 是周日，本周一为 2026-01-26
    days = week_dates(date(2026, 2, 1))
    assert days[0] == date(2026, 1, 26)
    assert days[-1] == date(2026, 2, 1)


def test_week_dates_cross_year():
    days = week_dates(date(2027, 1, 1))  # 周五
    assert days[0] == date(2026, 12, 28)
    assert days[3] == date(2026, 12, 31)
    assert days[4] == date(2027, 1, 1)


def test_datebar_initial_today_selected(qtbot):
    bar = DateBar()
    qtbot.addWidget(bar)
    assert bar.selected_date() == date.today()


def test_datebar_click_emits(qtbot):
    bar = DateBar()
    qtbot.addWidget(bar)
    target = date.today() + timedelta(days=2)
    fired = []
    bar.date_selected.connect(fired.append)
    bar._on_day_clicked(target)
    assert fired == [target]
    assert bar.selected_date() == target


def test_datebar_shift_week(qtbot):
    bar = DateBar()
    qtbot.addWidget(bar)
    anchor_before = bar._anchor
    bar.shift_week(7)
    assert bar._anchor == anchor_before + timedelta(days=7)
    bar.shift_week(-7)
    assert bar._anchor == anchor_before
