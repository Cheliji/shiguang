"""拾光应用入口。

当前（T03）仅启动一个空白主窗口，验证 PySide6 环境可用。
后续任务（T04/T22）将逐步替换为 FluentWindow 与完整启动序列。
"""

import sys

from PySide6.QtWidgets import QApplication, QMainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("拾光")

    window = QMainWindow()
    window.setWindowTitle("拾光")
    window.resize(1100, 720)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
