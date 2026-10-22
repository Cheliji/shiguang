"""TodoDialog 重复周期与日期联动测试（T11 初版，T24 重写为开始/结束日期 + 生成预览）。"""

from datetime import date

import pytest
from PySide6.QtCore import QDate
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
    assert dialog.preview_label.isHidden()
    assert dialog.yesButton.isEnabled()


def _set_range(dialog, repeat_index, start: QDate, end: QDate | None):
    dialog.repeat_combo.setCurrentIndex(repeat_index)
    dialog.start_picker.setDate(start)
    if end is not None:
        dialog.end_picker.setDate(end)


def test_repeat_requires_end_date(qtbot, window):
    """结束日期为空 → 红色提示 + 确认按钮禁用。"""
    dialog = TodoDialog(window)
    qtbot.addWidget(dialog)
    dialog.repeat_combo.setCurrentIndex(1)  # 每日
    assert dialog.date_stack.currentIndex() == 1
    assert dialog.preview_label.text() == "请选择结束日期"
    assert dialog.yesButton.isEnabled() is False


@pytest.mark.parametrize(
    ("repeat_index", "start", "end", "count"),
    [
        (1, QDate(2026, 10, 22), QDate(2026, 11, 1), 11),  # 每日
        (2, QDate(2026, 10, 22), QDate(2026, 11, 1), 2),  # 每周：10-22、10-29
        (3, QDate(2026, 10, 22), QDate(2027, 11, 1), 13),  # 每月：每月 22 日
    ],
)
def test_preview_count_matches_rules(qtbot, window, repeat_index, start, end, count):
    """生成条数预览与展开规则一致（示例取自产品文档 v0.5）。"""
    dialog = TodoDialog(window)
    qtbot.addWidget(dialog)
    _set_range(dialog, repeat_index, start, end)
    assert dialog.preview_label.text().startswith(f"将生成 {count} 条代办")
    assert "2026-10-22" in dialog.preview_label.text()  # 首条 = 开始日期
    assert dialog.yesButton.isEnabled()
    assert dialog.expanded_count() == count


def test_repeat_get_data_returns_range(qtbot, window):
    dialog = TodoDialog(window)
    qtbot.addWidget(dialog)
    _fill(dialog)
    _set_range(dialog, 1, QDate(2026, 10, 22), QDate(2026, 11, 1))
    data = dialog.get_data()
    assert data["repeat"] == "daily"
    assert data["day"] == date(2026, 10, 22)
    assert data["end_date"] == date(2026, 11, 1)
    assert "weekday" not in data and "month_day" not in data


def test_end_before_start_disables_confirm(qtbot, window):
    dialog = TodoDialog(window)
    qtbot.addWidget(dialog)
    _set_range(dialog, 1, QDate(2026, 11, 1), QDate(2026, 10, 22))
    assert dialog.preview_label.text() == "结束日期不能早于开始日期"
    assert dialog.yesButton.isEnabled() is False
    assert dialog.expanded_count() is None


def test_over_limit_disables_confirm(qtbot, window):
    dialog = TodoDialog(window)
    qtbot.addWidget(dialog)
    _set_range(dialog, 1, QDate(2026, 1, 1), QDate(2028, 1, 1))  # 每日两年 > 400 条
    assert "超过上限" in dialog.preview_label.text()
    assert dialog.yesButton.isEnabled() is False


def test_validate_backstop_rejects_invalid_range(qtbot, window):
    """即使绕过禁用按钮直接调 validate()，非法区间也不通过。"""
    dialog = TodoDialog(window)
    qtbot.addWidget(dialog)
    _fill(dialog)
    dialog.repeat_combo.setCurrentIndex(1)  # 每日，结束日期为空
    assert dialog.validate() is False


def test_edit_series_record_locked(qtbot, window):
    """编辑重复系列中的单条记录：重复区只读 + 提示文案，日期回显该记录自身日期。"""
    item = TodoItem(
        id=1,
        name="背单词",
        standard="20 个",
        date=date(2026, 10, 23),
        repeat="daily",
        series_id="s-1",
    )
    dialog = TodoDialog(window, item=item)
    qtbot.addWidget(dialog)
    assert dialog.repeat_combo.isEnabled() is False
    assert dialog.date_stack.isEnabled() is False
    assert dialog.repeat_hint.isHidden() is False
    assert dialog.preview_label.isHidden()
    assert dialog.yesButton.isEnabled()  # 其余字段仍可编辑
    _fill(dialog)
    data = dialog.get_data()
    assert "repeat" not in data and "day" not in data and "end_date" not in data


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
