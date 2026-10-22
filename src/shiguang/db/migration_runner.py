"""迁移执行入口：应用启动时调用 `upgrade_head()`，用户无感升级。"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from shiguang.config import get_db_path
from shiguang.db.session import sqlite_url_for

_ALEMBIC_INI = Path(__file__).resolve().parents[3] / "alembic.ini"
_MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def upgrade_head(db_path: Path | str | None = None) -> None:
    """将数据库升级到最新版本。

    `db_path` 为空时使用 `config.get_db_path()`（开发/生产由环境决定）；
    文件库会自动创建父目录。
    """
    path = db_path if db_path is not None else get_db_path()
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("script_location", str(_MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", sqlite_url_for(path))
    command.upgrade(cfg, "head")
