"""逾期自动延期扫描（T20）。

规则：计划日期早于今天且仍为待办 = 逾期；逾期且 delay_policy = "auto" = 需要顺延
（判断纯函数见 `domain/rules.py` 的 `needs_auto_delay`）。顺延 = 计划日期改为今天、
延期次数 +1，批量保存后发射 TaskService 的统一变更信号驱动 UI 刷新。

延期次数仅记录展示，不做惩罚（产品文档 §6）。启动接入与跨天定时器属 T22。
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session, sessionmaker

from shiguang.db.session import session_scope
from shiguang.domain.rules import needs_auto_delay
from shiguang.repositories.task_repository import TaskRepository
from shiguang.services.interfaces import TaskServiceInterface


class DelayService:
    """逾期 auto 代办顺延扫描。"""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        changed_emitter: TaskServiceInterface,
    ) -> None:
        self._factory = session_factory
        self._repo = TaskRepository()
        self._emit_changed = changed_emitter  # 统一变更信号（TaskService.changed）

    def scan(self, today: date | None = None) -> int:
        """顺延全部逾期 auto 代办，返回本次顺延数量。

        同一天重复执行是幂等的（已顺延到今天的记录不再视为逾期）；
        无顺延时返回 0 且不发射信号（避免无意义的整体刷新）。
        """
        today = today or date.today()
        with session_scope(self._factory) as s:
            overdue = self._repo.list_overdue(s, today)
            to_delay = [i for i in overdue if needs_auto_delay(i.date, i.delay_policy, today)]
            for item in to_delay:
                item.date = today
                item.delay_count += 1
                self._repo.save(s, item)
        if to_delay:
            self._emit_changed.changed.emit()
        return len(to_delay)
