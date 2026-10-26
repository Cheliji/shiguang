"""T18：真实代办服务单测（异常路径、过渡限制、重启持久化）。

契约行为见 test_task_service_contract.py（Mock / 真实实现共用）；
本文件只覆盖真实实现特有的错误类型、过渡限制与持久化。
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from shiguang.db.migration_runner import upgrade_head
from shiguang.db.session import create_engine_for, session_factory_for
from shiguang.models import Base
from shiguang.services.dto import REPEAT_DAILY, REPEAT_MONTHLY, REPEAT_WEEKLY
from shiguang.services.exceptions import (
    TaskArchivedError,
    TaskNotFoundError,
    TaskServiceError,
    ValidationError,
)
from shiguang.services.task_service import TaskService


def _make_service():
    """独立内存库 + 独立服务实例。"""
    engine = create_engine_for(":memory:")
    Base.metadata.create_all(engine)
    return TaskService(session_factory_for(engine)), engine


# ---------- 异常体系 ----------


def test_errors_subclass_value_error():
    """T05 契约：三类错误均继承 ValueError，UI `except ValueError` 继续有效。"""
    for cls in (ValidationError, TaskNotFoundError, TaskArchivedError):
        assert issubclass(cls, ValueError)
        assert issubclass(cls, TaskServiceError)


def test_blank_name_rejected():
    service, _ = _make_service()
    with pytest.raises(ValidationError):
        service.create_todo(name="   ", standard="标准")
    assert service.list_pending() == []  # 无残留


def test_blank_standard_rejected():
    service, _ = _make_service()
    with pytest.raises(ValidationError):
        service.create_todo(name="名称", standard="  ")
    assert service.list_pending() == []


# ---------- 重复代办创建时展开（T19） ----------


def test_repeat_daily_expands_to_independent_records():
    """每日：开始今天、结束 3 天后 → 连续 4 天各一条，共享系列标识。"""
    service, _ = _make_service()
    today = date.today()
    first = service.create_todo(
        name="背单词",
        standard="20 个",
        repeat=REPEAT_DAILY,
        day=today,
        end_date=today + timedelta(days=3),
    )
    series = service.list_pending()
    assert len(series) == 4
    assert [i.date for i in series] == [today + timedelta(days=i) for i in range(4)]
    assert len({i.series_id for i in series}) == 1
    assert first.series_id == series[0].series_id
    assert all(i.repeat == REPEAT_DAILY for i in series)


def test_repeat_weekly_expands():
    """每周：从 start 起每 7 天一条，不超过 end（10-22 ~ 11-01 → 2 条）。"""
    service, _ = _make_service()
    start, end = date(2026, 10, 22), date(2026, 11, 1)
    service.create_todo(name="周报", standard="发出", repeat=REPEAT_WEEKLY, day=start, end_date=end)
    series = service.list_pending()
    assert [i.date for i in series] == [date(2026, 10, 22), date(2026, 10, 29)]


def test_repeat_monthly_skips_month_without_day_number():
    """每月：1 月 31 日起，2 月无 31 日跳过 → 仅 1-31、3-31 两条。"""
    service, _ = _make_service()
    service.create_todo(
        name="月结",
        standard="完成",
        repeat=REPEAT_MONTHLY,
        day=date(2026, 1, 31),
        end_date=date(2026, 3, 31),
    )
    assert [i.date for i in service.list_pending()] == [date(2026, 1, 31), date(2026, 3, 31)]


def test_repeat_invalid_range_leaves_no_trace():
    """结束早于开始：拒绝创建且无残留。"""
    service, _ = _make_service()
    today = date.today()
    with pytest.raises(ValueError):
        service.create_todo(
            name="a",
            standard="s",
            repeat=REPEAT_DAILY,
            day=today,
            end_date=today - timedelta(days=1),
        )
    assert service.list_pending() == []


def test_repeat_expansion_atomic(tmp_path):
    """展开批量插入在同一事务：校验失败则全部不落库（跨连接验证无残留）。"""
    db = tmp_path / "t.db"
    upgrade_head(db)

    engine1 = create_engine_for(db)
    service1 = TaskService(session_factory_for(engine1))
    today = date.today()
    with pytest.raises(ValueError):
        # 结束日期早于开始日期：expand_dates 在批量插入前抛错
        service1.create_todo(
            name="a",
            standard="s",
            repeat=REPEAT_DAILY,
            day=today,
            end_date=today - timedelta(days=1),
        )
    engine1.dispose()

    engine2 = create_engine_for(db)
    service2 = TaskService(session_factory_for(engine2))
    assert service2.list_pending() == []
    engine2.dispose()


def test_update_missing_raises():
    service, _ = _make_service()
    with pytest.raises(TaskNotFoundError):
        service.update_todo(999, name="x")


def test_delete_missing_raises():
    service, _ = _make_service()
    with pytest.raises(TaskNotFoundError):
        service.delete_todo(999)


# ---------- 归档（T21） ----------


def test_archive_writes_back_single_row():
    """归档 = 单行更新：状态翻转 + 归档字段完整（含归档时间），不新增记录。"""
    from shiguang.services.dto import ArchiveInput

    service, _ = _make_service()
    item = service.create_todo(name="a", standard="s")
    archived = service.archive(item.id, ArchiveInput(duration=25, score=5, summary=" 不错 "))

    assert archived.status == "archived"
    assert (archived.score, archived.duration) == (5, 25)
    assert archived.summary == "不错"  # 去空白
    assert archived.archived_at is not None
    assert archived.date == item.date  # 计划日期不变

    assert service.list_pending() == []
    assert [i.id for i in service.list_archived()] == [item.id]


def test_archive_summary_length_limit():
    """总结非空时去空白且不超过 500 字。"""
    from shiguang.services.dto import ArchiveInput

    service, _ = _make_service()
    item = service.create_todo(name="a", standard="s")
    with pytest.raises(ValidationError, match="500"):
        service.archive(item.id, ArchiveInput(duration=10, score=5, summary="字" * 501))
    assert service.list_pending()[0].id == item.id  # 数据未变


def test_archive_invalid_input_leaves_no_trace(tmp_path):
    """评分/用时非法时拒绝且库无变化（跨连接验证）。"""
    from shiguang.services.dto import ArchiveInput

    db = tmp_path / "t.db"
    upgrade_head(db)

    engine1 = create_engine_for(db)
    service1 = TaskService(session_factory_for(engine1))
    item = service1.create_todo(name="a", standard="s")
    with pytest.raises(ValidationError):
        service1.archive(item.id, ArchiveInput(duration=10, score=6))
    with pytest.raises(ValidationError):
        service1.archive(item.id, ArchiveInput(duration=0, score=3))
    engine1.dispose()

    engine2 = create_engine_for(db)
    service2 = TaskService(session_factory_for(engine2))
    assert len(service2.list_pending()) == 1  # 仍是待办，无归档残留
    assert service2.list_archived() == []
    engine2.dispose()


def test_archive_missing_raises():
    from shiguang.services.dto import ArchiveInput

    service, _ = _make_service()
    with pytest.raises(TaskNotFoundError):
        service.archive(999, ArchiveInput(duration=10, score=5))


def test_archive_twice_rejected():
    from shiguang.services.dto import ArchiveInput

    service, _ = _make_service()
    item = service.create_todo(name="a", standard="s")
    service.archive(item.id, ArchiveInput(duration=10, score=5))
    with pytest.raises(TaskArchivedError):
        service.archive(item.id, ArchiveInput(duration=10, score=5))


def test_archive_persists_across_restart(tmp_path):
    """归档写入文件库，重启后已归档视图可见。"""
    from shiguang.services.dto import ArchiveInput

    db = tmp_path / "t.db"
    upgrade_head(db)

    engine1 = create_engine_for(db)
    service1 = TaskService(session_factory_for(engine1))
    item = service1.create_todo(name="重启后已归档", standard="s", day=date.today())
    service1.archive(item.id, ArchiveInput(duration=15, score=4, summary="完成"))
    engine1.dispose()

    engine2 = create_engine_for(db)
    service2 = TaskService(session_factory_for(engine2))
    archived = service2.list_archived(date.today())
    assert [i.name for i in archived] == ["重启后已归档"]
    assert archived[0].score == 4 and archived[0].duration == 15
    engine2.dispose()


# ---------- 行为细节 ----------


def test_create_defaults_day_to_today():
    """day 为空时计划日期默认为今天（契约测试 test_create_minimal 的语义）。"""
    service, _ = _make_service()
    item = service.create_todo(name="a", standard="s")
    assert item.date == date.today()
    assert [i.id for i in service.list_today(date.today())] == [item.id]


def test_update_rejects_blank_name():
    service, _ = _make_service()
    item = service.create_todo(name="a", standard="s")
    with pytest.raises(ValidationError):
        service.update_todo(item.id, name="   ")
    assert service.list_pending()[0].name == "a"  # 数据未变


def test_failed_create_leaves_no_trace(tmp_path):
    """校验失败不产生写入：新连接（新事务）视角下无残留记录。"""
    db = tmp_path / "t.db"
    upgrade_head(db)

    engine1 = create_engine_for(db)
    service1 = TaskService(session_factory_for(engine1))
    service1.create_todo(name="合法", standard="s")
    with pytest.raises(ValidationError):
        service1.create_todo(name=" ", standard="s")
    engine1.dispose()

    engine2 = create_engine_for(db)
    service2 = TaskService(session_factory_for(engine2))
    assert [i.name for i in service2.list_pending()] == ["合法"]
    engine2.dispose()


# ---------- 持久化（手工回归的自动化版） ----------


def test_data_survives_restart(tmp_path):
    """文件库：写入 → 关闭全部连接 → 重新打开（模拟重启）→ 数据仍在。"""
    db = tmp_path / "shiguang.db"
    upgrade_head(db)

    engine1 = create_engine_for(db)
    service1 = TaskService(session_factory_for(engine1))
    item = service1.create_todo(name="重启后仍在", standard="标准", day=date.today())
    engine1.dispose()

    engine2 = create_engine_for(db)
    service2 = TaskService(session_factory_for(engine2))
    items = service2.list_pending()
    assert [i.id for i in items] == [item.id]
    assert items[0].name == "重启后仍在"
    engine2.dispose()
