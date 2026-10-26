"""应用装配与启动序列（T22，技术设计文档 §5.1）。

启动序列：
    定位数据目录 → 初始化引擎并迁移到最新版本（幂等）
    → DelayService.scan() 逾期 auto 代办顺延（main.py 启动时执行一次）
    → 构建主窗口（main.py）→ DayRolloverWatcher 跨天定时器 + 窗口激活补检

说明：不再有"启动时补生成重复代办"步骤——重复代办创建时已一次性展开，
重启后自然各就其位。

USE_MOCK 为 True 时不做任何数据库初始化（Mock 内存数据，仅演示/测试用途）。
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from PySide6.QtCore import QEvent, QObject, QTimer
from sqlalchemy.engine import Engine

from shiguang import config
from shiguang.db.migration_runner import upgrade_head
from shiguang.db.session import create_engine_for, session_factory_for
from shiguang.services.delay_service import DelayService
from shiguang.services.interfaces import TaskServiceInterface
from shiguang.services.task_service import TaskService

# 跨天检查间隔：每分钟一次（技术设计文档 §5.1）
MIDNIGHT_CHECK_INTERVAL_MS = 60_000


def init_engine(db_path: Path | str | None = None) -> Engine:
    """定位数据目录（文件库自动建目录）并迁移到最新版本，返回引擎。"""
    path = db_path if db_path is not None else config.get_db_path()
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    upgrade_head(path)
    return create_engine_for(path)


def bootstrap_services(
    db_path: Path | str | None = None,
) -> tuple[TaskService, DelayService] | None:
    """装配真实服务：迁移 → TaskService + DelayService；USE_MOCK 时返回 None。"""
    if config.USE_MOCK:
        return None
    engine = init_engine(db_path)
    task_service = TaskService(session_factory_for(engine))
    delay_service = DelayService(session_factory_for(engine), task_service)
    return task_service, delay_service


class DayRolloverWatcher(QObject):
    """跨天监视：每分钟检查日期，跨天后顺延逾期 auto 代办并统一刷新 UI。

    - 同时给主窗口安装事件过滤：窗口激活（休眠/最小化恢复）时补做一次日期检查，
      覆盖系统休眠跨天场景；
    - UI 只订阅 TaskService.changed，本类复用该统一信号，UI 代码零改动；
    - 跨天当日多次触发（定时器 + 激活补检重叠）是幂等的：只认日期变化。
    """

    def __init__(
        self,
        task_service: TaskServiceInterface,
        delay_service: DelayService | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = task_service
        self._delay = delay_service
        self._last_day = date.today()
        self._timer = QTimer(self)
        self._timer.setInterval(MIDNIGHT_CHECK_INTERVAL_MS)
        self._timer.timeout.connect(self.check_day_rollover)
        self._timer.start()

    def install_on_window(self, window: QObject) -> None:
        """主窗口安装激活补检。"""
        window.installEventFilter(self)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802 (Qt API)
        if event.type() == QEvent.Type.WindowActivate:
            self.check_day_rollover()
        return False

    def check_day_rollover(self, today: date | None = None) -> bool:
        """日期检查：跨天则顺延 + 发射统一变更信号。返回是否发生跨天。

        today 可由调用方注入（跨天定时器与激活补检传 None，测试传固定日期）。
        """
        today = today or date.today()
        if today == self._last_day:
            return False
        self._last_day = today
        delayed = self._delay.scan(today) if self._delay is not None else 0
        if delayed == 0:
            # 无顺延时 scan 不发信号，由本类补发：保证每次跨天 UI 恰好刷新一次
            self._service.changed.emit()
        return True
