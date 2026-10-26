"""拾光应用入口。

T04：启动无边框主窗口（自绘标题栏 + 图标导航 + 占位页）。
T22：完整启动序列（数据目录定位 → 迁移 → 逾期顺延扫描 → 主窗口 → 跨天监视）。
"""

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
from qfluentwidgets import Theme, setTheme

from shiguang.ui.main_window import MainWindow

_QSS_PATH = Path(__file__).parent / "resources" / "styles.qss"


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("拾光")
    setTheme(Theme.LIGHT)

    # 字体栈（UI 设计文档 §2.2）：西文 Segoe UI，中文回退微软雅黑
    font = QFont()
    font.setFamilies(["Segoe UI", "Microsoft YaHei UI", "system-ui"])
    font.setPixelSize(14)
    app.setFont(font)

    if _QSS_PATH.exists():
        app.setStyleSheet(_QSS_PATH.read_text(encoding="utf-8"))

    # 开发期组件预览：SHIGUANG_PREVIEW=1 时展示预览窗口代替主窗口
    from shiguang.ui.pages.dev_preview_page import maybe_show_preview

    if maybe_show_preview():
        return app.exec()

    # T22 启动序列：迁移 → 逾期 auto 代办顺延扫描（真实服务；Mock 模式跳过）。
    # 本地 SQLite 迁移/扫描通常在毫秒级，等待光标作为启动耗时反馈。
    from shiguang.app import DayRolloverWatcher, bootstrap_services
    from shiguang.services import get_task_service, set_task_service

    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
    QApplication.processEvents()
    try:
        services = bootstrap_services()
        if services is not None:
            task_service, delay_service = services
            set_task_service(task_service)
            delay_service.scan()  # 启动时顺延一次逾期 auto 代办
        else:  # USE_MOCK=True：演示/测试模式，无数据库
            task_service, delay_service = get_task_service(), None
    finally:
        QApplication.restoreOverrideCursor()

    window = MainWindow()
    watcher = DayRolloverWatcher(task_service, delay_service, window)
    watcher.install_on_window(window)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
