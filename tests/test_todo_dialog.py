"""TodoDialog 测试（T10）。

MessageBoxBase 需要父窗口（遮罩依赖父窗口尺寸），测试中先建一个主窗口。
"""

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


def test_validate_requires_name_and_standard(qtbot, window):
    dialog = TodoDialog(window)
    qtbot.addWidget(dialog)
    assert dialog.validate() is False
    assert dialog.name_error.text()

    dialog.name_edit.setText("写周报")
    assert dialog.validate() is False  # 标准仍为空

    dialog.standard_edit.setPlainText("发出并收到确认")
    assert dialog.validate() is True


def test_get_data(qtbot, window):
    dialog = TodoDialog(window)
    qtbot.addWidget(dialog)
    dialog.name_edit.setText(" 写周报 ")
    dialog.desc_edit.setPlainText("描述")
    dialog.standard_edit.setPlainText(" 标准 ")
    data = dialog.get_data()
    assert data == {"name": "写周报", "description": "描述", "standard": "标准"}


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
