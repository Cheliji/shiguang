"""TaskService 接口契约测试（T05）。

针对接口行为编写，Mock 与真实实现（T18/T21）共用本测试。
"""

from datetime import date, timedelta

import pytest

from shiguang.services.dto import PRIORITY_RED, REPEAT_DAILY, ArchiveInput
from shiguang.services.mock.mock_task_service import MockTaskService


@pytest.fixture()
def service():
    """无预置数据的干净服务。"""
    return MockTaskService(with_seed=False)


# ---------- 创建 ----------


def test_create_minimal(service):
    item = service.create_todo(name=" 写周报 ", standard=" 发出并收到确认 ")
    assert item.id > 0
    assert item.name == "写周报"  # 去空白
    assert item.standard == "发出并收到确认"
    assert item.status == "pending"
    assert item.priority == "gray"  # 默认普通（灰）
    assert item in service.list_pending()


def test_create_with_priority(service):
    item = service.create_todo(name="a", standard="s", priority=PRIORITY_RED)
    assert item.priority == PRIORITY_RED


def test_update_priority(service):
    item = service.create_todo(name="a", standard="s")
    service.update_todo(item.id, priority=PRIORITY_RED)
    assert service.list_pending()[0].priority == PRIORITY_RED


def test_create_requires_name_and_standard(service):
    with pytest.raises(ValueError):
        service.create_todo(name="  ", standard="标准")
    with pytest.raises(ValueError):
        service.create_todo(name="名称", standard=" ")


def test_create_repeat_expands_series(service):
    """创建时展开：每日代办一次生成区间内全部独立记录，共享系列标识。"""
    today = date.today()
    first = service.create_todo(
        name="背单词",
        standard="20 个",
        repeat=REPEAT_DAILY,
        day=today,
        end_date=today + timedelta(days=7),
    )
    assert first.repeat == REPEAT_DAILY
    series = service.list_pending()
    assert len(series) == 8
    assert [i.date for i in series] == [today + timedelta(days=i) for i in range(8)]
    assert len({i.series_id for i in series}) == 1  # 同一系列
    assert all(i.series_id for i in series)


def test_create_repeat_requires_end_date(service):
    with pytest.raises(ValueError):
        service.create_todo(name="背单词", standard="20 个", repeat=REPEAT_DAILY, day=date.today())


def test_create_repeat_invalid_range_raises(service):
    today = date.today()
    with pytest.raises(ValueError):
        service.create_todo(
            name="a",
            standard="s",
            repeat=REPEAT_DAILY,
            day=today,
            end_date=today - timedelta(days=1),
        )
    with pytest.raises(ValueError):
        service.create_todo(
            name="a",
            standard="s",
            repeat=REPEAT_DAILY,
            day=today,
            end_date=today + timedelta(days=401),
        )
    assert service.list_pending() == []  # 校验失败无残留


def test_series_records_are_independent(service):
    """系列内记录互不影响：归档/删除一条不影响其余记录。"""
    today = date.today()
    first = service.create_todo(
        name="背单词",
        standard="20 个",
        repeat=REPEAT_DAILY,
        day=today,
        end_date=today + timedelta(days=2),
    )
    service.archive(first.id, ArchiveInput(duration=10, score=5))
    remaining = service.list_pending()
    assert len(remaining) == 2
    assert all(i.status == "pending" for i in remaining)
    service.delete_todo(remaining[0].id)
    assert len(service.list_pending()) == 1


def test_create_emits_changed(service):
    fired = []
    service.changed.connect(lambda: fired.append(1))
    service.create_todo(name="a", standard="b")
    assert fired == [1]


# ---------- 查询 ----------


def test_list_today(service):
    today = date.today()
    service.create_todo(name="今日事", standard="s", day=today)
    service.create_todo(name="明日事", standard="s", day=today + timedelta(days=1))
    assert [i.name for i in service.list_today(today)] == ["今日事"]


def test_today_summary(service):
    today = date.today()
    a = service.create_todo(name="a", standard="s", day=today)
    service.create_todo(name="b", standard="s", day=today)
    service.archive(a.id, ArchiveInput(duration=10, score=4))

    summary = service.today_summary(today)
    assert summary.total == 2
    assert summary.archived == 1
    assert summary.rate == pytest.approx(0.5)


def test_list_overdue(service):
    yesterday = date.today() - timedelta(days=1)
    service.create_todo(name="过期", standard="s", day=yesterday)
    service.create_todo(name="今日", standard="s", day=date.today())
    assert [i.name for i in service.list_overdue()] == ["过期"]


# ---------- 编辑 / 删除 ----------


def test_update_todo(service):
    item = service.create_todo(name="a", standard="s")
    service.update_todo(item.id, name="a2", description="d")
    assert service.list_pending()[0].name == "a2"
    assert service.list_pending()[0].description == "d"


def test_update_archived_raises(service):
    item = service.create_todo(name="a", standard="s")
    service.archive(item.id, ArchiveInput(duration=10, score=5))
    with pytest.raises(ValueError):
        service.update_todo(item.id, name="x")
    with pytest.raises(ValueError):
        service.delete_todo(item.id)


def test_delete_todo(service):
    item = service.create_todo(name="a", standard="s")
    service.delete_todo(item.id)
    assert service.list_pending() == []
    with pytest.raises(ValueError):
        service.delete_todo(item.id)  # 不存在


# ---------- 归档 ----------


def test_archive(service):
    item = service.create_todo(name="a", standard="s")
    service.archive(item.id, ArchiveInput(duration=25, score=5, summary=" 不错 "))
    archived = service.list_archived()
    assert len(archived) == 1
    assert archived[0].score == 5
    assert archived[0].duration == 25
    assert archived[0].summary == "不错"
    assert archived[0].archived_at is not None


def test_archive_summary_optional(service):
    """总结可选（产品文档 v0.3）。"""
    item = service.create_todo(name="a", standard="s")
    service.archive(item.id, ArchiveInput(duration=25, score=3))
    assert service.list_archived()[0].summary is None


@pytest.mark.parametrize("score", [0, 6])
def test_archive_invalid_score(service, score):
    item = service.create_todo(name="a", standard="s")
    with pytest.raises(ValueError):
        service.archive(item.id, ArchiveInput(duration=10, score=score))
    assert service.list_archived() == []  # 无残留


def test_archive_invalid_duration(service):
    item = service.create_todo(name="a", standard="s")
    with pytest.raises(ValueError):
        service.archive(item.id, ArchiveInput(duration=0, score=3))


def test_archive_twice_raises(service):
    item = service.create_todo(name="a", standard="s")
    service.archive(item.id, ArchiveInput(duration=10, score=4))
    with pytest.raises(ValueError):
        service.archive(item.id, ArchiveInput(duration=10, score=4))


# ---------- Mock 预置数据 ----------


def test_seed_data_covers_scenarios():
    service = MockTaskService(with_seed=True)
    today = date.today()
    assert len(service.list_today(today)) >= 3  # 普通 + 完成标准 + 每日重复
    assert len(service.list_overdue()) >= 1
    assert len(service.list_archived()) >= 2
