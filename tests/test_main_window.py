"""主窗口冒烟测试（T04）。"""

from PySide6.QtCore import Qt

from shiguang.ui.main_window import NAV_ITEMS, MainWindow


def test_window_is_frameless(qtbot):
    """无边框窗口：不依赖系统原生标题栏。"""
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.windowFlags() & Qt.WindowType.FramelessWindowHint


def test_title_bar(qtbot):
    """自绘标题栏存在且标题为"拾光"。"""
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.titleBar is not None
    assert window.windowTitle() == "拾光"


def test_navigation_switches_pages(qtbot):
    """5 个导航项，点击切换页面容器。"""
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.nav.button_count() == len(NAV_ITEMS) == 5
    assert window.stack.count() == 5
    assert window.stack.currentIndex() == 0  # 默认"今日"

    for index in range(5):
        window.nav.select(index)
        assert window.stack.currentIndex() == index


def test_window_size_constraints(qtbot):
    """默认 1100x720，最小 960x640。"""
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.size().width() == 1100
    assert window.size().height() == 720
    assert window.minimumWidth() == 960
    assert window.minimumHeight() == 640
