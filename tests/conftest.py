"""pytest 全局配置：Qt 使用离屏平台，避免 CI/无显示环境弹窗。"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# T22：产品默认已切换为真实实现（USE_MOCK=False），但 UI 测试不允许触碰
# 真实数据库文件——测试进程强制走 Mock，数据层测试自行构建独立内存库。
from shiguang import config  # noqa: E402

config.USE_MOCK = True
