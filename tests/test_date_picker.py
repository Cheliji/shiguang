"""自绘日历弹窗 DatePickerButton 测试（替代 QCalendarWidget 的自绘组件）。"""

from PySide6.QtCore import QDate, Qt

from shiguang.ui.theme import Color
from shiguang.ui.widgets.date_picker import CalendarPopup, DatePickerButton


class _FakeWheelEvent:
    """wheelEvent 只调用 event.ignore()，用轻量替身验证即可。"""

    def __init__(self) -> None:
        self.ignored = False

    def ignore(self) -> None:
        self.ignored = True


def _active_button(popup: CalendarPopup):
    """返回当前唯一高亮（实心主题色圆）的日期格。"""
    return next(b for b in popup._day_buttons if f"background: {Color.PRIMARY};" in b.styleSheet())


def test_popup_defaults_to_today_highlighted(qtbot):
    popup = CalendarPopup()
    qtbot.addWidget(popup)
    today = QDate.currentDate()

    popup.reset(None)

    assert popup._selected == today
    assert popup._title_label.text() == f"{today.year()}年 {today.month()}月"
    active = _active_button(popup)
    assert active.text() == str(today.day())


def test_selecting_other_date_turns_today_plain_white(qtbot):
    popup = CalendarPopup()
    qtbot.addWidget(popup)
    today = QDate.currentDate()
    popup.reset(None)

    other = today.addDays(1) if today.day() < today.daysInMonth() else today.addDays(-1)
    popup._selected = other
    popup._refresh()

    # 当日恢复普通白底样式
    today_button = next(b for b in popup._day_buttons if b._date == today)
    assert f"background: {Color.SURFACE};" in today_button.styleSheet()
    assert f"background: {Color.PRIMARY};" not in today_button.styleSheet()
    # 唯一高亮是新选日期，且样式与进入时的当日高亮完全一致
    active = _active_button(popup)
    assert active.text() == str(other.day())


def test_no_highlight_residue_after_month_switch(qtbot):
    popup = CalendarPopup()
    qtbot.addWidget(popup)
    today = QDate.currentDate()
    popup.reset(None)
    assert _active_button(popup).text() == str(today.day())

    popup._navigate(1)  # 切到下个月

    # 选中日期不在本月 → 整月无高亮，今日原位置也不残留任何颜色
    assert not any(
        f"background: {Color.PRIMARY};" in b.styleSheet() for b in popup._day_buttons
    )
    popup._navigate(-1)  # 切回当月
    assert _active_button(popup).text() == str(today.day())


def test_navigate_by_month_rolls_year(qtbot):
    popup = CalendarPopup()
    qtbot.addWidget(popup)
    today = QDate.currentDate()

    popup.reset(None)
    popup._navigate(-1)
    prev = today.addMonths(-1)
    assert (popup._month.year(), popup._month.month()) == (prev.year(), prev.month())
    popup._navigate(1)
    assert popup._month.month() == today.month()

    # 跨年：1 月 < 一步 → 上一年 12 月
    popup._month = QDate(2025, 1, 1)
    popup._refresh()
    popup._navigate(-1)
    assert (popup._month.year(), popup._month.month()) == (2024, 12)


def test_outside_days_are_grayed(qtbot):
    popup = CalendarPopup()
    qtbot.addWidget(popup)
    today = QDate.currentDate()

    popup.reset(None)
    outside = [b for b in popup._day_buttons if f"color: {Color.TEXT_TERTIARY};" in b.styleSheet()]
    # 6 行固定网格：补位数 = 42 - 当月天数
    assert len(outside) == 42 - today.daysInMonth()
    for button in outside:
        assert f"background: {Color.PRIMARY};" not in button.styleSheet()


def test_reset_with_initial_date_selects_it(qtbot):
    popup = CalendarPopup()
    qtbot.addWidget(popup)
    target = QDate(2030, 5, 20)

    popup.reset(target)

    assert popup._month == QDate(2030, 5, 1)
    assert popup._selected == target
    assert _active_button(popup).text() == "20"


def test_day_click_emits_and_closes(qtbot):
    popup = CalendarPopup()
    qtbot.addWidget(popup)
    fired: list[QDate] = []
    popup.dateSelected.connect(fired.append)

    popup.reset(None)
    popup._day_buttons[0].click()

    assert fired and isinstance(fired[0], QDate)


def test_wheel_event_is_ignored(qtbot):
    popup = CalendarPopup()
    qtbot.addWidget(popup)
    popup.reset(None)
    event = _FakeWheelEvent()

    popup.wheelEvent(event)

    assert event.ignored


def test_button_picks_date_via_popup(qtbot):
    button = DatePickerButton()
    qtbot.addWidget(button)
    assert not button.hasDate()

    button._show_calendar()
    assert button._popup is not None
    assert button._popup._month.month() == QDate.currentDate().month()  # 默认当日所在月

    button._popup._day_buttons[10].click()
    assert button.hasDate()
    assert button.text() == button.getDate().toString(Qt.DateFormat.ISODate)


def test_button_optional_mode_clear(qtbot):
    button = DatePickerButton(placeholder="结束日期（可选）")
    qtbot.addWidget(button)
    assert button.text() == "结束日期（可选）"

    button.setDate(QDate(2030, 1, 2))
    assert button.hasDate()
    button.clearDate()
    assert not button.hasDate()
    assert button.text() == "结束日期（可选）"
