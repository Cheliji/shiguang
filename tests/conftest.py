"""pytest 全局配置：Qt 使用离屏平台，避免 CI/无显示环境弹窗。"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
