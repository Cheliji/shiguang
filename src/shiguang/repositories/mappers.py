"""Task ORM 模型与 TodoItem DTO 的双向转换（T17）。

与 T05 的 `services.dto.TodoItem` 对齐：已归档项附带评分/用时/总结/归档时间，
含 priority 重要程度透传。仓储层出入参一律经本模块转换，不向服务层泄露 ORM 实体。
"""

from __future__ import annotations

from shiguang.models.task import Task
from shiguang.services.dto import TodoItem

# TodoItem 可表示、且可写回 ORM 实体的字段（id 由数据库自增，不参与写回）
_SHARED_FIELDS = (
    "name",
    "standard",
    "description",
    "date",
    "repeat",
    "priority",
    "series_id",
    "delay_policy",
    "delay_count",
    "status",
    "score",
    "duration",
    "summary",
    "archived_at",
)


def task_to_dto(task: Task) -> TodoItem:
    """ORM 实体 → DTO（None 文本列归一为 ""，与 Mock 行为一致）。"""
    return TodoItem(
        id=task.id,
        name=task.name,
        standard=task.standard or "",
        description=task.description or "",
        date=task.date,
        repeat=task.repeat,
        priority=task.priority,
        series_id=task.series_id,
        delay_policy=task.delay_policy,
        delay_count=task.delay_count,
        status=task.status,
        score=task.score,
        duration=task.duration,
        summary=task.summary,
        archived_at=task.archived_at,
    )


def dto_to_task(item: TodoItem) -> Task:
    """DTO → ORM 新实体（用于新增；id 由数据库自增忽略）。"""
    return Task(**{field: getattr(item, field) for field in _SHARED_FIELDS})


def apply_dto(task: Task, item: TodoItem) -> None:
    """把 DTO 字段写回已有实体（用于更新；id 不变）。"""
    for field in _SHARED_FIELDS:
        setattr(task, field, getattr(item, field))
