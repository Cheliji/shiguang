"""基于 SQLite 的真实代办服务（T18）。

与 Mock 的差异 / 本阶段有意不做的部分（按任务文档，后续任务补齐）：
- 重复代办（repeat != "none"）暂以校验错误拒绝 —— T19 接入创建时展开生成；
- 归档入口暂抛 NotImplementedError —— T21 接入（单行更新）；
- 自动延期扫描 —— T20 接入。

行为约定（与 Mock 对齐，契约测试共用同一套断言）：
- name / standard 去空白后必填，否则抛 ValidationError；
- day 为空时计划日期默认为今天（repeat = "none"）；
- 列表排序：按重要程度降序（红>橙>蓝>绿>灰），同档按日期/id 升序；
- 已归档记录不可编辑/删除；不存在的 id 抛 TaskNotFoundError；
- 每次数据变更提交成功后发射 `changed` 信号。
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.orm import Session, sessionmaker

from shiguang.db.session import session_scope
from shiguang.repositories.task_repository import TaskRepository
from shiguang.services.dto import (
    REPEAT_NONE,
    STATUS_ARCHIVED,
    ArchiveInput,
    TodaySummary,
    TodoItem,
    priority_rank,
)
from shiguang.services.exceptions import (
    TaskArchivedError,
    TaskNotFoundError,
    ValidationError,
)
from shiguang.services.interfaces import TaskServiceInterface

_REPEAT_UNSUPPORTED = "重复代办将在后续版本支持，当前请创建「不重复」代办"


class TaskService(TaskServiceInterface):
    """真实代办服务：经仓储层读写 SQLite，业务规则在本层。"""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        super().__init__()
        self._factory = session_factory
        self._repo = TaskRepository()

    # ---------- 查询 ----------

    def list_today(self, day: date) -> list[TodoItem]:
        with session_scope(self._factory) as s:
            items = self._repo.list_by_date(s, day)
        return sorted(items, key=lambda i: (priority_rank(i.priority), i.id))

    def list_pending(self) -> list[TodoItem]:
        with session_scope(self._factory) as s:
            items = self._repo.list_pending(s)
        return sorted(
            items, key=lambda i: (priority_rank(i.priority), i.date or date.max, i.id)
        )

    def list_overdue(self) -> list[TodoItem]:
        return [i for i in self.list_pending() if i.is_overdue()]

    def list_archived(self, day: date | None = None) -> list[TodoItem]:
        with session_scope(self._factory) as s:
            items = self._repo.list_archived(s, day)
        return sorted(items, key=lambda i: i.archived_at or datetime.min, reverse=True)

    def list_todo_dates(self) -> set[date]:
        with session_scope(self._factory) as s:
            return self._repo.dates_with_todos(s, date.min, date.max)

    def today_summary(self, day: date) -> TodaySummary:
        with session_scope(self._factory) as s:
            total, archived = self._repo.count_for_day(s, day)
        return TodaySummary(total=total, archived=archived)

    # ---------- 变更 ----------

    def create_todo(
        self,
        name: str,
        standard: str,
        description: str = "",
        day: date | None = None,
        repeat: str = REPEAT_NONE,
        end_date: date | None = None,
        priority: str = "gray",
        delay_policy: str = "default",
    ) -> TodoItem:
        name_s = name.strip()
        standard_s = standard.strip()
        if not name_s:
            raise ValidationError("代办名称不能为空")
        if not standard_s:
            raise ValidationError("完成标准不能为空")
        if repeat != REPEAT_NONE:
            # T18 过渡限制：T19 接入创建时展开生成后解除
            raise ValidationError(_REPEAT_UNSUPPORTED)

        item = TodoItem(
            id=0,
            name=name_s,
            standard=standard_s,
            description=description.strip(),
            date=day or date.today(),
            repeat=repeat,
            priority=priority,
            delay_policy=delay_policy,
        )
        with session_scope(self._factory) as s:
            created = self._repo.add(s, item)
        self.changed.emit()
        return created

    def update_todo(self, task_id: int, **fields) -> TodoItem:
        with session_scope(self._factory) as s:
            item = self._require_pending(s, task_id, action="编辑")
            if "name" in fields:
                name = str(fields["name"]).strip()
                if not name:
                    raise ValidationError("代办名称不能为空")
                item.name = name
            if "standard" in fields:
                standard = str(fields["standard"]).strip()
                if not standard:
                    raise ValidationError("完成标准不能为空")
                item.standard = standard
            for key in ("description", "date", "priority", "delay_policy"):
                if key in fields:
                    setattr(item, key, fields[key])
            updated = self._repo.save(s, item)
        self.changed.emit()
        return updated

    def delete_todo(self, task_id: int) -> None:
        with session_scope(self._factory) as s:
            self._require_pending(s, task_id, action="删除")
            self._repo.delete(s, task_id)
        self.changed.emit()

    def archive(self, task_id: int, data: ArchiveInput) -> TodoItem:
        # T18 有意不做：T21 接入真实归档（单行更新）。
        raise NotImplementedError("归档功能将在后续版本提供（T21 接入）")

    # ---------- 内部 ----------

    def _require_pending(self, session: Session, task_id: int, action: str) -> TodoItem:
        """取待办记录；不存在 / 已归档分别抛对应错误（消息与 Mock 对齐）。"""
        item = self._repo.get(session, task_id)
        if item is None:
            raise TaskNotFoundError(f"代办不存在: {task_id}")
        if item.status == STATUS_ARCHIVED:
            raise TaskArchivedError(f"已归档代办不可{action}")
        return item
