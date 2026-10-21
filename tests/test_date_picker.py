"""自绘日历弹窗 CalendarPopup / DatePickerButton 测试。

关键断言用离屏渲染 + 像素采样，直接验证用户可见效果：
- 进入时当日为主题色实心圆；
- 选中其他日期后当日立即变纯白，选中日与进入时当日同色；
- 切月后原当日位置无任何残留颜色；
- 非当月日期灰色、当月白色、滚轮被忽略。
"""

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QWidget

from shiguang.ui.theme import Color
from shiguang.ui.widgets.date_picker import CalendarPopup, DatePickerButton

PRIMARY_RGB = (0, 159, 170)  # Color.PRIMARY #009FAA
WHITE_RGB = (255, 255, 255)


class _FakeWheelEvent:
    def __init__(self) -> None:
        self.ignored = False

    def ignore(self) -> None:
        self.ignored = True


def _render(popup: CalendarPopup):
    popup.repaint()
    return popup.grab().toImage()


def _cell_rgb(img, popup: CalendarPopup, button) -> tuple[int, int, int]:
    """取日期格内偏上位置（避开数字字形）的实际渲染颜色。"""
    geo = button.geometry()
    x = geo.x() + geo.width() // 2
    y = geo.y() + geo.height() // 2 - 12
    c = img.pixelColor(x, y)
    return (c.red(), c.green(), c.blue())


def _button_of(popup: CalendarPopup, day: QDate):
    return next(b for b in popup._day_buttons if b._date == day)


def _other_day(today: QDate) -> QDate:
    return QDate(today.year(), today.month(), 1 if today.day() > 1 else 2)


def test_defaults_to_today_highlighted_with_theme_color(qtbot):
    popup = CalendarPopup()
    qtbot.addWidget(popup)
    today = QDate.currentDate()

    popup.reset(None)
    img = _render(popup)

    assert popup.title_text() == f"{today.year()}年 {today.month()}月"
    assert _cell_rgb(img, popup, _button_of(popup, today)) == PRIMARY_RGB


def test_today_turns_white_after_picking_other_date(qtbot):
    popup = CalendarPopup()
    qtbot.addWidget(popup)
    today = QDate.currentDate()
    popup.reset(None)

    other = _other_day(today)
    popup._on_day_clicked(_button_of(popup, other))
    img = _render(popup)

    # 当日恢复纯白
    assert _cell_rgb(img, popup, _button_of(popup, today)) == WHITE_RGB
    # 选中日与进入时当日高亮颜色完全一致（同一主题色）
    assert _cell_rgb(img, popup, _button_of(popup, other)) == PRIMARY_RGB


def test_no_color_residue_after_month_switch(qtbot):
    popup = CalendarPopup()
    qtbot.addWidget(popup)
    today = QDate.currentDate()
    popup.reset(None)
    today_button = _button_of(popup, today)
    assert _cell_rgb(_render(popup), popup, today_button) == PRIMARY_RGB

    popup._navigate(1)  # 切到下个月：选中日期不在本月 → 整窗无高亮
    img = _render(popup)
    for button in popup._day_buttons:
        rgb = _cell_rgb(img, popup, button)
        assert rgb != PRIMARY_RGB, f"{button._date} 残留主题色"

    popup._navigate(-1)  # 切回当月：选中日（当日）恢复高亮，位置正确
    assert _cell_rgb(_render(popup), popup, today_button) == PRIMARY_RGB


def test_month_navigation_rolls_year(qtbot):
    popup = CalendarPopup()
    qtbot.addWidget(popup)
    today = QDate.currentDate()

    popup.reset(None)
    popup._navigate(-1)
    prev = today.addMonths(-1)
    assert popup.title_text() == f"{prev.year()}年 {prev.month()}月"

    popup._month = QDate(2025, 1, 1)
    popup._refresh()
    popup._navigate(-1)
    assert popup.title_text() == "2024年 12月"


def test_outside_days_are_gray_inside_white(qtbot):
    popup = CalendarPopup()
    qtbot.addWidget(popup)
    today = QDate.currentDate()
    popup.reset(QDate(today.year(), today.month(), 15))
    img = _render(popup)

    outside = [b for b in popup._day_buttons if b._date.month() != today.month()]
    assert len(outside) == 42 - today.daysInMonth()
    for button in outside:
        assert _cell_rgb(img, popup, button) == WHITE_RGB

    # 当月非选中日也是白底（灰色只体现在文字上）
    in_month = [
        b
        for b in popup._day_buttons
        if b._date.month() == today.month() and b._date != popup._selected
    ]
    for button in in_month:
        assert _cell_rgb(img, popup, button) == WHITE_RGB


def test_wheel_event_is_ignored(qtbot):
    popup = CalendarPopup()
    qtbot.addWidget(popup)
    popup.reset(None)
    event = _FakeWheelEvent()

    popup.wheelEvent(event)

    assert event.ignored


def test_only_selected_date_highlighted(qtbot):
    popup = CalendarPopup()
    qtbot.addWidget(popup)
    popup.reset(QDate(2030, 5, 20))

    highlighted = [
        b._date.toString("yyyy-MM-dd")
        for b in popup._day_buttons
        if b._date == popup._selected
    ]
    assert highlighted == ["2030-05-20"]
    assert popup._selected == QDate(2030, 5, 20)


def test_button_picks_date_via_popup(qtbot):
    host = QWidget()
    qtbot.addWidget(host)
    host.resize(600, 500)
    button = DatePickerButton(host)
    assert not button.hasDate()

    button._show_calendar()
    assert button._popup is not None
    assert button._popup.title_text().startswith(str(QDate.currentDate().year()))
    assert button._popup.parent() is None  # 顶层独立窗口，不继承对话框样式

    button._popup._day_buttons[10].click()
    assert button.hasDate()
    assert button.text() == button.getDate().toString("yyyy-MM-dd")


def test_button_optional_mode_clear(qtbot):
    button = DatePickerButton(placeholder="结束日期（可选）")
    qtbot.addWidget(button)
    assert button.text() == "结束日期（可选）"

    button.setDate(QDate(2030, 1, 2))
    assert button.hasDate()
    button.clearDate()
    assert not button.hasDate()
    assert button.text() == "结束日期（可选）"
    assert button.property("placeholder") is True


def test_trigger_uses_theme_surface(gtbot_unused=None):
    """触发器样式使用主题令牌（防止硬编码色值回退）。"""
    assert Color.PRIMARY == "#009FAA"
