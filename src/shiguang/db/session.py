"""SQLite 引擎与会话管理。

所有工厂均为函数形式（延迟创建），禁止在模块 import 时创建全局 engine。
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

MEMORY_PATH = ":memory:"


def sqlite_url_for(path: Path | str) -> str:
    """由数据库文件路径构造 SQLite URL；`":memory:"` 表示内存库。"""
    if str(path) == MEMORY_PATH:
        return "sqlite:///:memory:"
    return f"sqlite:///{Path(path).as_posix()}"


def create_engine_for(path: Path | str) -> Engine:
    """创建 SQLite 引擎。

    - WAL 日志模式（单机单进程，提升读并发）
    - 打开外键约束（SQLite 默认关闭）
    - 内存库使用 StaticPool，保证同一引擎的多次连接共享同一份数据
    """
    url = sqlite_url_for(path)
    kwargs: dict = {}
    if str(path) == MEMORY_PATH:
        kwargs = {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}
    engine = create_engine(url, **kwargs)

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _record):  # noqa: ANN001, ANN202
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def session_factory_for(engine: Engine) -> sessionmaker[Session]:
    """创建会话工厂。`expire_on_commit=False` 便于提交后仍可读实体属性。"""
    return sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    """事务会话上下文：正常结束自动 commit，异常 rollback，最终 close。"""
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
