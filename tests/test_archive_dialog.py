"""ArchiveDialog 测试（T13）。"""

from datetime import date

import pytest
from PySide6.QtWidgets import QMainWindow

from shiguang.services.dto import TodoItem
from shiguang.ui.dialogs.archive_dialog import ArchiveDialog


@pytest.fixture()
def window(qtbot):
    win = QMainWindow()
    win.resize(1100, 720)
    qtbot.addWidget(win)
    return win


def _item() -> TodoItem:
    return TodoItem(
        id=5,
        name="晨跑 5 公里",
        standard="配速低于 6:00",
        description="天气好就出门",
        date=date.today(),
    )


def test_readonly_info_display(qtbot, window):
    dialog = ArchiveDialog(window, item=_item())
    qtbot.addWidget(dialog)
    assert dialog.name_label.text() == "晨跑 5 公里"
    assert dialog.standard_text.text() == "配速低于 6:00"
    assert dialog.desc_label.text() == "天气好就出门"


def test_confirm_disabled_until_score(qtbot, window):
    dialog = ArchiveDialog(window, item=_item())
    qtbot.addWidget(dialog)
    assert dialog.yesButton.isEnabled() is False  # 未评分
    dialog.rating.set_score(4)
    assert dialog.yesButton.isEnabled() is True  # 用时默认 30 > 0
    dialog.rating.set_score(0)
    assert dialog.yesButton.isEnabled() is False


def test_quick_duration(qtbot, window):
    dialog = ArchiveDialog(window, item=_item())
    qtbot.addWidget(dialog)
    dialog._on_quick_duration(45)
    assert dialog.duration_spin.value() == 45


def test_get_data_summary_optional(qtbot, window):
    dialog = ArchiveDialog(window, item=_item())
    qtbot.addWidget(dialog)
    dialog.rating.set_score(5)
    dialog.duration_spin.setValue(20)
    dialog.summary_edit.setPlainText("不错")
    data = dialog.get_data()
    assert data.duration == 20
    assert data.score == 5
    assert data.summary == "不错"


def test_counter(qtbot, window):
    dialog = ArchiveDialog(window, item=_item())
    qtbot.addWidget(dialog)
    dialog.summary_edit.setPlainText("x" * 460)
    assert "460" in dialog.counter_label.text()
    assert Color_WARNING(dialog.counter_label.styleSheet())


def Color_WARNING(stylesheet: str) -> bool:
    from shiguang.ui.theme import Color

    return Color.WARNING in stylesheet
