"""T16：Task 单表模型与迁移（任务 + 归档记录合一，技术设计文档 v0.2 §4.2）。"""

from __future__ import annotations

from datetime import date, datetime

import pytest
from sqlalchemy import inspect, text

from shiguang.db.migration_runner import upgrade_head
from shiguang.db.session import create_engine_for, session_factory_for, session_scope
from shiguang.models import Base, Task
from shiguang.services import dto


@pytest.fixture()
def factory():
    """内存 SQLite：直接按模型元数据建表。"""
    engine = create_engine_for(":memory:")
    Base.metadata.create_all(engine)
    yield session_factory_for(engine)
    engine.dispose()


def test_enum_constants_match_dto():
    """DTO 字符串常量即枚举成员值（UI 零改动）。"""
    assert dto.REPEAT_NONE == "none" and dto.REPEAT_DAILY == "daily"
    assert dto.DELAY_DEFAULT == "default" and dto.DELAY_AUTO == "auto"
    assert dto.STATUS_PENDING == "pending" and dto.STATUS_ARCHIVED == "archived"


def test_create_pending_defaults(factory):
    """待办记录：默认 kind/period/repeat/status/delay，归档字段为空。"""
    with session_scope(factory) as s:
        s.add(Task(name="写周报", standard="发出并确认", date=date(2026, 10, 22)))

    with session_scope(factory) as s:
        task = s.query(Task).one()
    assert task.kind == "todo"
    assert task.period == "day"
    assert task.repeat == "none"
    assert task.status == "pending"
    assert task.delay_policy == "default"
    assert task.delay_count == 0
    assert task.series_id is None
    # 归档字段待办时为空
    assert task.duration is None
    assert task.score is None
    assert task.summary is None
    assert task.archived_at is None
    assert task.created_at is not None and task.updated_at is not None


def test_archive_fields_written_back_on_same_row(factory):
    """归档 = 同一行写入用时/评分/总结/归档时间并翻转状态（不新增记录）。"""
    with session_scope(factory) as s:
        s.add(Task(name="晨跑", standard="配速低于 6:00", date=date(2026, 10, 22)))

    with session_scope(factory) as s:
        task = s.query(Task).one()
        task.status = dto.STATUS_ARCHIVED
        task.duration = 30
        task.score = 4
        task.summary = "状态不错"
        task.archived_at = datetime(2026, 10, 22, 7, 30)

    with session_scope(factory) as s:
        assert s.query(Task).count() == 1  # 仍只有一条记录
        task = s.query(Task).one()
    assert task.status == "archived"
    assert (task.duration, task.score, task.summary) == (30, 4, "状态不错")
    assert task.archived_at == datetime(2026, 10, 22, 7, 30)


def test_repeat_series_records_share_series_id(factory):
    """重复展开生成的记录共享 series_id，各自独立（无模板/实例之分）。"""
    with session_scope(factory) as s:
        for i in range(3):
            s.add(
                Task(
                    name="背单词",
                    standard="20 个",
                    date=date(2026, 10, 22 + i),
                    repeat="daily",
                    series_id="s-1",
                )
            )

    with session_scope(factory) as s:
        rows = s.query(Task).filter_by(series_id="s-1").all()
    assert len(rows) == 3
    assert {r.date for r in rows} == {date(2026, 10, 22 + i) for i in range(3)}


def test_upgrade_head_creates_tasks_table(tmp_path):
    """迁移后表结构与模型一致（列 + 索引）。"""
    db = tmp_path / "t.db"
    upgrade_head(db)

    engine = create_engine_for(db)
    columns = {c["name"] for c in inspect(engine).get_columns("tasks")}
    indexes = {i["name"] for i in inspect(engine).get_indexes("tasks")}
    engine.dispose()

    expected = {
        "id",
        "name",
        "kind",
        "period",
        "repeat",
        "series_id",
        "date",
        "delay_policy",
        "delay_count",
        "related_task_ids",
        "description",
        "standard",
        "status",
        "duration",
        "score",
        "summary",
        "archived_at",
        "created_at",
        "updated_at",
    }
    assert expected <= columns
    assert {"ix_tasks_status_date", "ix_tasks_series_id"} <= indexes

    # 无模板/归档记录旧设计的残留
    assert "template_id" not in columns
    assert "end_date" not in columns
    assert "weekday" not in columns
    assert "month_day" not in columns

    engine = create_engine_for(db)
    with engine.connect() as conn:
        tables = (
            conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).scalars().all()
        )
    engine.dispose()
    assert "archive_records" not in tables
