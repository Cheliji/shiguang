"""拾光应用入口。

T04：启动无边框主窗口（自绘标题栏 + 图标导航 + 占位页）。
T22 将加入完整启动序列（数据库迁移、实例生成、延期扫描）。
"""

import sys
from pathlib import Path

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

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
