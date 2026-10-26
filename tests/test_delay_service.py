"""T20：自动延期服务单测（内存库 + 文件库）。

覆盖：auto 顺延且计数递增（连续两天各 +1）；default/never 不变；
今日待办不受影响；同日重复扫描幂等；已归档不参与扫描；信号发射。
"""

from __future__ import annotations

from datetime import date, timedelta

from shiguang.db.session import create_engine_for, session_factory_for
from shiguang.models import Base
from shiguang.services.delay_service import DelayService
from shiguang.services.dto import DELAY_AUTO, DELAY_DEFAULT, DELAY_NEVER
from shiguang.services.task_service import TaskService


def _make():
    engine = create_engine_for(":memory:")
    Base.metadata.create_all(engine)
    service = TaskService(session_factory_for(engine))
    return service, DelayService(session_factory_for(engine), service)


def _overdue(service, name, delay_policy, days_back=1):
    item = service.create_todo(name=name, standard="s", day=date.today())
    return service.update_todo(
        item.id, date=date.today() - timedelta(days=days_back), delay_policy=delay_policy
    )


def test_auto_overdue_delayed_with_count():
    service, delay = _make()
    _overdue(service, "逾期 auto", DELAY_AUTO)

    fired = []
    service.changed.connect(lambda: fired.append(1))

    assert delay.scan() == 1
    items = service.list_today(date.today())
    assert [i.name for i in items] == ["逾期 auto"]
    assert items[0].date == date.today()
    assert items[0].delay_count == 1  # 卡片展示"已延期 1 次"
    assert fired == [1]  # 统一变更信号驱动 UI 刷新


def test_default_and_never_untouched():
    service, delay = _make()
    _overdue(service, "默认策略", DELAY_DEFAULT)
    _overdue(service, "不延期", DELAY_NEVER)

    fired = []
    service.changed.connect(lambda: fired.append(1))

    assert delay.scan() == 0
    overdue = service.list_overdue()
    assert {i.name for i in overdue} == {"默认策略", "不延期"}
    assert all(i.delay_count == 0 for i in overdue)
    assert all(i.date < date.today() for i in overdue)  # 原日期不动
    assert fired == []  # 无顺延不发信号


def test_today_pending_unaffected():
    service, delay = _make()
    service.create_todo(name="今日事", standard="s", day=date.today())
    assert delay.scan() == 0
    assert [i.name for i in service.list_today(date.today())] == ["今日事"]


def test_same_day_rescan_is_idempotent():
    service, delay = _make()
    _overdue(service, "逾期 auto", DELAY_AUTO)
    assert delay.scan() == 1
    assert delay.scan() == 0  # 已顺延到今天，不再视为逾期
    assert service.list_today(date.today())[0].delay_count == 1


def test_consecutive_days_increment_count():
    """连续逾期多天：每天扫描一次，延期次数逐天 +1。"""
    service, delay = _make()
    _overdue(service, "逾期 auto", DELAY_AUTO, days_back=2)

    assert delay.scan(date.today()) == 1
    assert delay.scan(date.today() + timedelta(days=1)) == 1
    item = service.list_today(date.today() + timedelta(days=1))[0]
    assert item.delay_count == 2
    assert item.date == date.today() + timedelta(days=1)


def test_archived_never_delayed():
    from shiguang.services.dto import ArchiveInput

    service, delay = _make()
    item = _overdue(service, "已归档逾期", DELAY_AUTO)
    service.archive(item.id, ArchiveInput(duration=10, score=5))
    assert delay.scan() == 0
    archived = service.list_archived(date.today())
    assert archived[0].date < date.today()  # 计划日期保持昨天
    assert archived[0].delay_count == 0


def test_needs_auto_delay_pure_function():
    from shiguang.domain.rules import needs_auto_delay

    today = date.today()
    yesterday = today - timedelta(days=1)
    assert needs_auto_delay(yesterday, "auto", today) is True
    assert needs_auto_delay(yesterday, "default", today) is False
    assert needs_auto_delay(yesterday, "never", today) is False
    assert needs_auto_delay(today, "auto", today) is False  # 今日不逾期
    assert needs_auto_delay(None, "auto", today) is False
