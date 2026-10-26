"""全局配置。

- `USE_MOCK`：UI 实现阶段使用内存 Mock 数据；阶段四（T18 起）切换为 False
- `get_db_path()`：SQLite 数据库文件路径（T15）
  - 生产：`%APPDATA%/Shiguang/shiguang.db`（platformdirs 解析）
  - 开发（默认）：项目根目录 `./data/shiguang-dev.db`
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from platformdirs import user_data_dir

# 阶段四数据层已落地（T22）：默认使用真实数据库服务；
# Mock 仅保留测试/演示用途，改回 True 即可一键切回
USE_MOCK = False

APP_NAME = "拾光"

_PROD_DB_NAME = "shiguang.db"
_DEV_DB_NAME = "shiguang-dev.db"


def is_frozen() -> bool:
    """是否运行在 PyInstaller 打包产物中。"""
    return getattr(sys, "frozen", False)


def _project_root() -> Path:
    # src/shiguang/config.py -> 项目根目录
    return Path(__file__).resolve().parents[2]


def bundle_root() -> Path:
    """资源根目录：冻结态为 PyInstaller 解包目录，开发态为项目根目录。"""
    if is_frozen():
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return _project_root()


def package_root() -> Path:
    """shiguang 包根目录：冻结态为解包目录内的包副本，开发态为 src/shiguang。"""
    if is_frozen():
        return Path(sys._MEIPASS) / "shiguang"  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent


def get_db_path() -> Path:
    """返回当前环境的数据库文件路径（不创建文件）。

    打包产物（frozen）一律使用平台数据目录 `%APPDATA%/Shiguang/shiguang.db`，
    与 exe 本体解耦：更新 exe 不影响用户数据。
    开发环境由环境变量 `SHIGUANG_ENV` 决定：`production` 走平台数据目录，
    其他取值（含缺省）使用项目根目录下的 `data/`。
    """
    if is_frozen() or os.environ.get("SHIGUANG_ENV") == "production":
        return Path(user_data_dir("Shiguang")) / _PROD_DB_NAME
    return _project_root() / "data" / _DEV_DB_NAME
