"""T22：启动序列集成测试 + 跨天监视器单测。

集成测试模拟日期下端到端启动：上一会话留下逾期 auto 代办 → 冷启动
（bootstrap_services 重新装配）→ 启动扫描 → 顺延且延期次数 +1。
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from PySide6.QtCore import QEvent

from shiguang import config
from shiguang.app import (
    MIDNIGHT_CHECK_INTERVAL_MS,
    DayRolloverWatcher,
    bootstrap_services,
    init_engine,
)
from shiguang.db.session import create_engine_for, session_factory_for
from shiguang.services.dto import DELAY_AUTO, REPEAT_DAILY
from shiguang.services.task_service import TaskService


@pytest.fixture()
def real_mode(monkeypatch):
    """数据层测试需要真实实现：覆盖 conftest 的 USE_MOCK=True。"""
    monkeypatch.setattr(config, "USE_MOCK", False)


# ---------- init_engine / bootstrap_services ----------


def test_init_engine_creates_and_migrates_db(tmp_path):
    db = tmp_path / "sub" / "shiguang.db"  # 父目录不存在也会自动创建
    engine = init_engine(db)
    assert db.exists()
    with engine.connect() as conn:
        tables = conn.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'").scalars()
        assert {"tasks", "alembic_version"} <= set(tables)
    engine.dispose()


def test_bootstrap_services_returns_none_when_mock():
    assert config.USE_MOCK is True  # conftest 强制
    assert bootstrap_services() is None


def test_bootstrap_services_real(real_mode, tmp_path):
    db = tmp_path / "t.db"
    services = bootstrap_services(db)
    assert services is not None
    task_service, delay_service = services
    assert delay_service.scan() == 0  # 空库无逾期
    item = task_service.create_todo(name="a", standard="s")
    assert item.id > 0


# ---------- 启动序列端到端（模拟日期/冷启动） ----------


def test_startup_scan_delays_overdue_auto(real_mode, tmp_path):
    """上一会话留下逾期 auto 代办 → 冷启动重新装配 + 启动扫描 → 顺延且 +1。"""
    db = tmp_path / "t.db"
    yesterday = date.today() - timedelta(days=1)

    # 上一次会话：创建 auto 代办并逾期（会话结束后引擎即"关机"）
    engine1 = init_engine(db)
    prev = TaskService(session_factory_for(engine1))
    item = prev.create_todo(name="逾期 auto", standard="s", day=date.today())
    prev.update_todo(item.id, date=yesterday, delay_policy=DELAY_AUTO)
    engine1.dispose()

    # 冷启动：bootstrap 重新装配（迁移幂等），随后 main.py 会执行 scan()
    task_service, delay_service = bootstrap_services(db)
    assert delay_service.scan() == 1

    today_items = task_service.list_today(date.today())
    assert [i.name for i in today_items] == ["逾期 auto"]
    assert today_items[0].date == date.today()  # 红条消失：已是今日
    assert today_items[0].delay_count == 1  # "已延期 1 次"


def test_startup_keeps_repeat_series_without_regeneration(real_mode, tmp_path):
    """checklist：每日代办创建时已展开，重启后无需"启动补生成"自然各就其位。"""
    db = tmp_path / "t.db"
    yesterday = date.today() - timedelta(days=1)
    tomorrow = date.today() + timedelta(days=1)

    engine1 = init_engine(db)
    prev = TaskService(session_factory_for(engine1))
    prev.create_todo(
        name="每日", standard="s", repeat=REPEAT_DAILY, day=yesterday, end_date=tomorrow
    )
    engine1.dispose()

    task_service, _ = bootstrap_services(db)  # 冷启动，无补生成步骤
    assert [i.name for i in task_service.list_today(date.today())] == ["每日"]
    assert len(task_service.list_pending()) == 3  # 昨天/今天/明天各一条，不增不减


# ---------- 跨天监视器 ----------


def _watcher_setup():
    engine = create_engine_for(":memory:")
    from shiguang.models import Base

    Base.metadata.create_all(engine)
    service = TaskService(session_factory_for(engine))
    from shiguang.services.delay_service import DelayService

    return service, DayRolloverWatcher(service, DelayService(session_factory_for(engine), service))


def test_watcher_same_day_no_rollover():
    service, watcher = _watcher_setup()
    fired = []
    service.changed.connect(lambda: fired.append(1))
    today = date.today()
    assert watcher.check_day_rollover(today) is False
    assert watcher.check_day_rollover(today + timedelta(days=1) - timedelta(days=1)) is False
    assert fired == []


def test_watcher_rollover_scans_and_emits_once():
    service, watcher = _watcher_setup()
    item = service.create_todo(name="逾期 auto", standard="s", day=date.today())
    service.update_todo(item.id, date=date.today() - timedelta(days=1), delay_policy=DELAY_AUTO)

    fired = []
    service.changed.connect(lambda: fired.append(1))

    today = date.today()
    assert watcher.check_day_rollover(today + timedelta(days=1)) is True
    assert service.list_today(today + timedelta(days=1))[0].delay_count == 1
    assert fired == [1]

    # 同一天再查（定时器 + 激活补检重叠）幂等：不重复顺延/刷新
    assert watcher.check_day_rollover(today + timedelta(days=1)) is False
    assert fired == [1]


def test_watcher_window_activate_triggers_check(qtbot):
    service, watcher = _watcher_setup()
    window = watcher.parent()  # None；用一个真实窗口验证事件过滤
    from PySide6.QtWidgets import QMainWindow

    window = QMainWindow()
    qtbot.addWidget(window)
    watcher.install_on_window(window)

    calls = []
    watcher.check_day_rollover = lambda *a, **k: calls.append(1) or False
    assert watcher.eventFilter(window, QEvent(QEvent.Type.WindowActivate)) is False
    assert calls == [1]


def test_watcher_timer_configured():
    _, watcher = _watcher_setup()
    assert watcher._timer.interval() == MIDNIGHT_CHECK_INTERVAL_MS == 60_000
    assert watcher._timer.isActive()
