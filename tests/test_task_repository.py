"""T17：TaskRepository 单测（内存库）。

覆盖任务文档列出的全部存取能力：基础存取、列表查询（按日期/待办/逾期/已归档）、
辅助查询（圆点日期/今日概览）、统计预留（按归档日期分组）。
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from shiguang.db.session import create_engine_for, session_factory_for, session_scope
from shiguang.models import Base
from shiguang.repositories.task_repository import TaskRepository
from shiguang.services.dto import (
    PRIORITY_RED,
    STATUS_ARCHIVED,
    STATUS_PENDING,
    TodoItem,
)

DAY = date(2026, 10, 22)
YESTERDAY = DAY - timedelta(days=1)
TOMORROW = DAY + timedelta(days=1)


@pytest.fixture()
def factory():
    """内存 SQLite：按模型元数据建表。"""
    engine = create_engine_for(":memory:")
    Base.metadata.create_all(engine)
    yield session_factory_for(engine)
    engine.dispose()


@pytest.fixture()
def repo():
    return TaskRepository()


def _item(**kwargs) -> TodoItem:
    kwargs.setdefault("name", "代办")
    kwargs.setdefault("standard", "标准")
    kwargs.setdefault("date", DAY)
    item_id = kwargs.pop("id", 0)
    return TodoItem(id=item_id, **kwargs)


def _add(session: Session, repo: TaskRepository, **kwargs) -> TodoItem:
    return repo.add(session, _item(**kwargs))


# ---------- 基础存取 ----------


def test_add_and_get_roundtrip(factory, repo):
    with session_scope(factory) as s:
        created = _add(
            s,
            repo,
            name=" 写周报 ",
            standard=" 发出并确认 ",
            description="周五前",
            priority=PRIORITY_RED,
        )
        assert created.id > 0
        fetched = repo.get(s, created.id)

    assert fetched is not None
    assert fetched.name == " 写周报 "  # 去空白在服务层，仓储原样存取
    assert fetched.standard == " 发出并确认 "
    assert fetched.description == "周五前"
    assert fetched.priority == PRIORITY_RED
    assert fetched.status == STATUS_PENDING
    assert isinstance(fetched, TodoItem)


def test_get_missing_returns_none(factory, repo):
    with session_scope(factory) as s:
        assert repo.get(s, 999) is None


def test_save_updates_fields(factory, repo):
    with session_scope(factory) as s:
        created = _add(s, repo, name="旧名")
        created.name = "新名"
        created.priority = PRIORITY_RED
        created.date = TOMORROW
        saved = repo.save(s, created)

        fetched = repo.get(s, created.id)
    assert saved.name == "新名"
    assert fetched.name == "新名"
    assert fetched.priority == PRIORITY_RED
    assert fetched.date == TOMORROW


def test_save_missing_raises(factory, repo):
    with pytest.raises(ValueError, match="任务不存在"):
        with session_scope(factory) as s:
            repo.save(s, _item(id=999))


def test_delete(factory, repo):
    with session_scope(factory) as s:
        created = _add(s, repo)
        repo.delete(s, created.id)
        assert repo.get(s, created.id) is None
        repo.delete(s, created.id)  # 重复删除静默忽略


# ---------- 列表查询 ----------


def _seed_three(factory, repo):
    """昨天（已归档）/ 今天 / 明天（待办），外加一条逾期待办。"""
    with session_scope(factory) as s:
        done = _add(
            s,
            repo,
            name="昨日已完成",
            date=YESTERDAY,
            status=STATUS_ARCHIVED,
            score=4,
            duration=30,
            summary="不错",
            archived_at=datetime.combine(DAY, datetime.min.time()).replace(hour=8),
        )
        _add(s, repo, name="今天的事", date=DAY)
        _add(s, repo, name="明天的事", date=TOMORROW)
        _add(s, repo, name="逾期的债", date=YESTERDAY - timedelta(days=1))
    return done


def test_list_by_date_filters_status(factory, repo):
    _seed_three(factory, repo)
    with session_scope(factory) as s:
        pending = repo.list_by_date(s, DAY)
        archived = repo.list_by_date(s, DAY, STATUS_ARCHIVED)
        empty = repo.list_by_date(s, DAY + timedelta(days=9))
    assert [i.name for i in pending] == ["今天的事"]
    assert archived == []
    assert empty == []


def test_list_pending(factory, repo):
    _seed_three(factory, repo)
    with session_scope(factory) as s:
        items = repo.list_pending(s)
    assert {i.name for i in items} == {"今天的事", "明天的事", "逾期的债"}
    assert all(i.status == STATUS_PENDING for i in items)


def test_list_overdue(factory, repo):
    _seed_three(factory, repo)
    with session_scope(factory) as s:
        items = repo.list_overdue(s, DAY)
    assert [i.name for i in items] == ["逾期的债"]  # 昨日已归档的不算逾期


def test_list_archived_all_and_by_day(factory, repo):
    done = _seed_three(factory, repo)
    with session_scope(factory) as s:
        all_items = repo.list_archived(s)
        # 按归档时间过滤：该记录计划日期是昨天，但归档时间是今天
        today_hit = repo.list_archived(s, DAY)
        yesterday_miss = repo.list_archived(s, YESTERDAY)

    assert [i.id for i in all_items] == [done.id]
    assert all_items[0].score == 4  # 归档字段透传
    assert all_items[0].duration == 30
    assert all_items[0].summary == "不错"
    assert all_items[0].archived_at is not None
    assert [i.id for i in today_hit] == [done.id]
    assert yesterday_miss == []


def test_archived_passthrough_priority(factory, repo):
    with session_scope(factory) as s:
        created = _add(
            s,
            repo,
            status=STATUS_ARCHIVED,
            priority=PRIORITY_RED,
            archived_at=datetime(2026, 10, 22, 7, 30),
        )
        fetched = repo.get(s, created.id)
    assert fetched.priority == PRIORITY_RED


# ---------- 辅助查询 ----------


def test_dates_with_todos(factory, repo):
    _seed_three(factory, repo)
    with session_scope(factory) as s:
        in_range = repo.dates_with_todos(s, YESTERDAY, TOMORROW)
        narrow = repo.dates_with_todos(s, TOMORROW, TOMORROW)
        empty = repo.dates_with_todos(s, TOMORROW + timedelta(days=1), TOMORROW + timedelta(days=2))
    # 仅待办：昨天那条已归档不产出圆点日期；逾期项（10-20）不在查询范围内
    assert in_range == {DAY, TOMORROW}
    assert narrow == {TOMORROW}
    assert empty == set()


def test_count_for_day(factory, repo):
    """总数 = 当日待办 + 当日归档；归档数以归档时间为准。"""
    _seed_three(factory, repo)
    with session_scope(factory) as s:
        # 今天：1 条当日待办 + 1 条今日归档（计划日期为昨天）
        assert repo.count_for_day(s, DAY) == (2, 1)
        # 昨天：无当日待办；归档时间不是昨天 → 0
        assert repo.count_for_day(s, YESTERDAY) == (0, 0)
        # 无数据日期
        assert repo.count_for_day(s, DAY + timedelta(days=9)) == (0, 0)


def test_count_archived_by_date(factory, repo):
    _seed_three(factory, repo)
    with session_scope(factory) as s:
        repo.add(
            s,
            _item(
                name="另一条今日归档",
                status=STATUS_ARCHIVED,
                archived_at=datetime.combine(DAY, datetime.min.time()).replace(hour=20),
            ),
        )
        repo.add(
            s,
            _item(
                name="昨天归档",
                date=YESTERDAY,
                status=STATUS_ARCHIVED,
                archived_at=datetime.combine(YESTERDAY, datetime.min.time()).replace(hour=18),
            ),
        )
        counts = repo.count_archived_by_date(s)
    assert counts == {DAY: 2, YESTERDAY: 1}


def test_count_archived_by_date_empty(factory, repo):
    with session_scope(factory) as s:
        assert repo.count_archived_by_date(s) == {}


# ---------- 边界 ----------


def test_empty_results_are_empty_lists(factory, repo):
    with session_scope(factory) as s:
        assert repo.list_pending(s) == []
        assert repo.list_overdue(s, DAY) == []
        assert repo.list_archived(s) == []
        assert repo.list_archived(s, DAY) == []
        assert repo.dates_with_todos(s, DAY, TOMORROW) == set()


def test_returns_dto_not_orm(factory, repo):
    """返回值中不出现 ORM 实体/查询对象，均为纯 TodoItem DTO。"""
    _seed_three(factory, repo)
    with session_scope(factory) as s:
        results = [
            repo.get(s, 1),
            *repo.list_by_date(s, DAY),
            *repo.list_pending(s),
            *repo.list_overdue(s, DAY),
            *repo.list_archived(s),
        ]
    assert all(type(item) is TodoItem for item in results)  # noqa: E721
