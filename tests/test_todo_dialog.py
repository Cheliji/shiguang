"""TodoDialog 重复周期与日期联动测试（T11）。"""

from datetime import date

import pytest
from PySide6.QtWidgets import QMainWindow

from shiguang.services.dto import TodoItem
from shiguang.ui.dialogs.todo_dialog import TodoDialog


@pytest.fixture()
def window(qtbot):
    win = QMainWindow()
    win.resize(1100, 720)
    qtbot.addWidget(win)
    return win


def _fill(dialog):
    dialog.name_edit.setText("测试")
    dialog.standard_edit.setPlainText("标准")


def test_validate_requires_name_and_standard(qtbot, window):
    dialog = TodoDialog(window)
    qtbot.addWidget(dialog)
    assert dialog.validate() is False
    assert dialog.name_error.text()
    dialog.name_edit.setText("写周报")
    assert dialog.validate() is False
    dialog.standard_edit.setPlainText("发出并收到确认")
    assert dialog.validate() is True


def test_get_data_basic_fields(qtbot, window):
    dialog = TodoDialog(window)
    qtbot.addWidget(dialog)
    dialog.name_edit.setText(" 写周报 ")
    dialog.desc_edit.setPlainText("描述")
    dialog.standard_edit.setPlainText(" 标准 ")
    data = dialog.get_data()
    assert data["name"] == "写周报"
    assert data["description"] == "描述"
    assert data["standard"] == "标准"
    assert data["repeat"] == "none"
    assert data["day"] is not None


def test_edit_mode_prefill(qtbot, window):
    item = TodoItem(id=7, name="旧名称", standard="旧标准", description="旧描述")
    dialog = TodoDialog(window, item=item)
    qtbot.addWidget(dialog)
    assert dialog.name_edit.text() == "旧名称"
    assert dialog.standard_edit.toPlainText() == "旧标准"
    assert dialog.yesButton.text() == "保存修改"
    assert dialog.edit_item_id() == 7


def test_guide_hides_after_input(qtbot, window):
    dialog = TodoDialog(window)
    qtbot.addWidget(dialog)
    dialog.standard_edit.setPlainText("有内容了")
    assert dialog._guide.isHidden()


def test_default_repeat_none(qtbot, window):
    dialog = TodoDialog(window)
    qtbot.addWidget(dialog)
    assert dialog.repeat_combo.currentData() == "none"
    assert dialog.date_stack.currentIndex() == 0


def test_daily_returns_range(qtbot, window):
    dialog = TodoDialog(window)
    qtbot.addWidget(dialog)
    dialog.repeat_combo.setCurrentIndex(1)  # 每日
    assert dialog.date_label.text() == "开始日期"
    _fill(dialog)
    data = dialog.get_data()
    assert data["repeat"] == "daily"
    assert data["end_date"] is None  # 长期默认勾选

    dialog.long_term_check.setChecked(False)
    data = dialog.get_data()
    assert data["end_date"] is not None


def test_weekly_stores_single_weekday(qtbot, window):
    dialog = TodoDialog(window)
    qtbot.addWidget(dialog)
    dialog.repeat_combo.setCurrentIndex(2)  # 每周
    _fill(dialog)
    dialog.weekday_buttons[0].setChecked(True)
    dialog.weekday_buttons[3].setChecked(True)  # 单选：后选取消前者
    assert dialog.weekday_buttons[0].isChecked() is False
    data = dialog.get_data()
    assert data["weekday"] == 3


def test_monthly_stores_month_day(qtbot, window):
    dialog = TodoDialog(window)
    qtbot.addWidget(dialog)
    dialog.repeat_combo.setCurrentIndex(3)  # 每月
    _fill(dialog)
    dialog.month_day_buttons[14].setChecked(True)  # 15 号
    data = dialog.get_data()
    assert data["month_day"] == 15


def test_edit_repeat_instance_locked(qtbot, window):
    item = TodoItem(
        id=1,
        name="背单词",
        standard="20 个",
        date=date.today(),
        repeat="daily",
        end_date=None,
    )
    dialog = TodoDialog(window, item=item)
    qtbot.addWidget(dialog)
    assert dialog.repeat_combo.isEnabled() is False
    assert dialog.date_stack.isEnabled() is False


def test_delay_policy_default_and_auto(qtbot, window):
    dialog = TodoDialog(window)
    qtbot.addWidget(dialog)
    _fill(dialog)
    assert dialog.get_data()["delay_policy"] == "default"
    dialog.delay_buttons["auto"].setChecked(True)
    assert dialog.get_data()["delay_policy"] == "auto"


def test_goal_placeholder_disabled(qtbot, window):
    dialog = TodoDialog(window)
    qtbot.addWidget(dialog)
    assert dialog.goal_edit.isEnabled() is False
