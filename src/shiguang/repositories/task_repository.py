"""tasks 表仓储：全部查询与持久化封装（T17）。

设计约定（全项目统一，写进模块文档以便对照）：

- **无业务规则**：本层只做数据存取；排序、校验、默认值等业务逻辑归服务层与
  领域层，列表查询不保证返回顺序。
- **会话由调用方传入**：服务层经 `db.session.session_scope` 打开事务并把
  `Session` 作为第一个参数传入；仓储不自行创建会话、不提交/回滚事务——
  重复代办批量展开等写入必须由服务层保证在同一事务内完成。
- **出入参均为 DTO / 纯 Python 值**：返回 `services.dto.TodoItem` 或
  date / int / tuple / dict 等纯值，绝不返回 ORM 查询对象或实体。

表内每条记录都是要展示的代办，查询无需"排除模板"之类的特例（无模板/实例之分）。
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from shiguang.models.task import Task
from shiguang.repositories.mappers import apply_dto, dto_to_task, task_to_dto
from shiguang.services.dto import STATUS_ARCHIVED, STATUS_PENDING, TodoItem


class TaskRepository:
    """tasks 表存取。方法第一个参数均为调用方管理的 Session。"""

    # ---------- 基础存取 ----------

    def add(self, session: Session, item: TodoItem) -> TodoItem:
        """新增一条记录，返回带自增 id 的 DTO。"""
        task = dto_to_task(item)
        session.add(task)
        session.flush()
        return task_to_dto(task)

    def get(self, session: Session, task_id: int) -> TodoItem | None:
        """按 id 查询；不存在返回 None。"""
        task = session.get(Task, task_id)
        return task_to_dto(task) if task is not None else None

    def save(self, session: Session, item: TodoItem) -> TodoItem:
        """按 id 写回全部可变字段；记录不存在时抛 ValueError。"""
        task = session.get(Task, item.id)
        if task is None:
            raise ValueError(f"任务不存在: {item.id}")
        apply_dto(task, item)
        session.flush()
        return task_to_dto(task)

    def delete(self, session: Session, task_id: int) -> None:
        """按 id 删除；不存在时静默忽略（调用方已做存在性校验）。"""
        task = session.get(Task, task_id)
        if task is not None:
            session.delete(task)
            session.flush()

    # ---------- 列表查询 ----------

    def list_by_date(
        self, session: Session, day: date, status: str = STATUS_PENDING
    ) -> list[TodoItem]:
        """指定日期 + 状态的记录（今日页 / 代办页"今日"与"待办"视图）。"""
        stmt = select(Task).where(Task.date == day, Task.status == status)
        return [task_to_dto(t) for t in session.scalars(stmt)]

    def list_pending(self, session: Session) -> list[TodoItem]:
        """全部待办记录。"""
        stmt = select(Task).where(Task.status == STATUS_PENDING)
        return [task_to_dto(t) for t in session.scalars(stmt)]

    def list_overdue(self, session: Session, today: date) -> list[TodoItem]:
        """计划日期早于 today 且仍为待办的记录。"""
        stmt = select(Task).where(Task.status == STATUS_PENDING, Task.date < today)
        return [task_to_dto(t) for t in session.scalars(stmt)]

    def list_archived(self, session: Session, day: date | None = None) -> list[TodoItem]:
        """已归档记录；day 非空时按归档时间（archived_at，非计划日期）过滤。"""
        stmt = select(Task).where(Task.status == STATUS_ARCHIVED)
        if day is not None:
            stmt = stmt.where(func.date(Task.archived_at) == day)
        return [task_to_dto(t) for t in session.scalars(stmt)]

    # ---------- 辅助查询 ----------

    def dates_with_todos(self, session: Session, start: date, end: date) -> set[date]:
        """[start, end] 范围内哪些日期有待办（DateBar 圆点）。"""
        stmt = select(Task.date).where(
            Task.status == STATUS_PENDING, Task.date >= start, Task.date <= end
        )
        return set(session.scalars(stmt))

    def count_for_day(self, session: Session, day: date) -> tuple[int, int]:
        """今日概览计数，返回 (今日总数, 已归档数)。

        总数 = 当日计划待办 + 当日归档；归档数以归档时间（archived_at）为准。
        """
        pending = session.scalar(
            select(func.count())
            .select_from(Task)
            .where(Task.status == STATUS_PENDING, Task.date == day)
        )
        archived = session.scalar(
            select(func.count())
            .select_from(Task)
            .where(func.date(Task.archived_at) == day)
        )
        return (pending or 0) + (archived or 0), archived or 0

    def count_archived_by_date(self, session: Session) -> dict[date, int]:
        """按归档日期分组计数（热力图用，本阶段只实现不接线）。"""
        stmt = (
            select(func.date(Task.archived_at), func.count())
            .where(Task.status == STATUS_ARCHIVED, Task.archived_at.is_not(None))
            .group_by(func.date(Task.archived_at))
        )
        result: dict[date, int] = {}
        for day_key, count in session.execute(stmt):
            day = day_key if isinstance(day_key, date) else date.fromisoformat(str(day_key))
            result[day] = count
        return result
