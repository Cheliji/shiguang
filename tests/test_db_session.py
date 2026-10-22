"""T15：db/session 提交与回滚、迁移入口（测试全部使用内存库 / 临时目录）。"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from shiguang.db.migration_runner import upgrade_head
from shiguang.db.session import (
    create_engine_for,
    session_factory_for,
    session_scope,
    sqlite_url_for,
)


@pytest.fixture()
def factory():
    """内存 SQLite：预建一张临时表，返回会话工厂。"""
    engine = create_engine_for(":memory:")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE t (id INTEGER PRIMARY KEY, name VARCHAR(50))"))
    yield session_factory_for(engine)
    engine.dispose()


def test_sqlite_url_for():
    assert sqlite_url_for(":memory:") == "sqlite:///:memory:"
    assert sqlite_url_for("data/x.db").startswith("sqlite:///")


def test_engine_pragmas():
    """外键约束开启；文件库为 WAL 模式（内存库 journal_mode 退化为 memory）。"""
    engine = create_engine_for(":memory:")
    with engine.connect() as conn:
        assert conn.execute(text("PRAGMA foreign_keys")).scalar() == 1
    engine.dispose()


def test_session_scope_commit_visible(factory):
    with session_scope(factory) as s:
        s.execute(text("INSERT INTO t (name) VALUES ('a')"))

    with session_scope(factory) as s:
        rows = s.execute(text("SELECT name FROM t")).all()
    assert rows == [("a",)]


def test_session_scope_rollback_on_error(factory):
    with pytest.raises(RuntimeError, match="boom"):
        with session_scope(factory) as s:
            s.execute(text("INSERT INTO t (name) VALUES ('a')"))
            raise RuntimeError("boom")

    with session_scope(factory) as s:
        count = s.execute(text("SELECT COUNT(*) FROM t")).scalar()
    assert count == 0


def test_upgrade_head_creates_dev_db(tmp_path):
    """upgrade_head 在空目录创建库文件并写入 alembic_version。"""
    db = tmp_path / "sub" / "shiguang-dev.db"
    upgrade_head(db)

    assert db.exists()
    engine = create_engine_for(db)
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    engine.dispose()

    # 已盖到当前 head（与迁移脚本目录一致，不硬编码版本号）
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cfg = Config("alembic.ini")
    cfg.set_main_option("script_location", "src/shiguang/db/migrations")
    assert version == ScriptDirectory.from_config(cfg).get_current_head()
