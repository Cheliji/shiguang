"""Task ORM 模型（技术设计文档 v0.2 §4.2）。

代办与目标统一表（MVP 只用 kind='todo'）；**任务与归档记录合一**：
归档 = 在本行写入 duration / score / summary / archived_at 并翻转 status，
待办时归档字段为 NULL。

无模板/实例之分：repeat != 'none' 的记录即创建时展开生成的普通代办记录，
series_id 标识同批（同一 UUID），每条独立展示、独立归档。
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from shiguang.domain.enums import DelayPolicy, Period, Priority, Repeat, TaskKind, TaskStatus
from shiguang.models.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(10), default=TaskKind.TODO.value)
    period: Mapped[str] = mapped_column(String(10), default=Period.DAY.value)
    repeat: Mapped[str] = mapped_column(
        String(10), default=Repeat.NONE.value, server_default=Repeat.NONE.value
    )  # 创建时选择的重复规则
    series_id: Mapped[str | None] = mapped_column(
        String(36)
    )  # 同一次重复展开生成的记录共享（UUID）；不重复为 NULL
    priority: Mapped[str] = mapped_column(
        String(10), default=Priority.GRAY.value, server_default=Priority.GRAY.value
    )  # 重要程度五色：red/orange/blue/green/gray（递减，gray=普通）
    date: Mapped[date] = mapped_column(Date)  # 计划日期（每条记录对应一个具体日期）
    delay_policy: Mapped[str] = mapped_column(
        String(10), default=DelayPolicy.DEFAULT.value, server_default=DelayPolicy.DEFAULT.value
    )
    delay_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )  # 自动延期次数（仅记录展示）
    related_task_ids: Mapped[list[int] | None] = mapped_column(JSON)  # 关联目标（v1.0 启用）
    description: Mapped[str | None] = mapped_column(Text)
    standard: Mapped[str | None] = mapped_column(Text)  # 代办流程/完成标准
    status: Mapped[str] = mapped_column(
        String(10), default=TaskStatus.PENDING.value, server_default=TaskStatus.PENDING.value
    )
    # ---- 归档字段（status='pending' 时为 NULL，归档时写回本行） ----
    duration: Mapped[int | None] = mapped_column(Integer)  # 用时（分钟）
    score: Mapped[int | None] = mapped_column(Integer)  # 质量评分 1–5
    summary: Mapped[str | None] = mapped_column(Text)  # 总结（可选）
    archived_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_tasks_status_date", "status", "date"),
        Index("ix_tasks_series_id", "series_id"),
    )
