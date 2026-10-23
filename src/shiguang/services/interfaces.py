"""服务接口契约。

UI 层只依赖本模块定义的接口与 DTO，不感知 Mock / 真实实现（SQLAlchemy）。
接口签名即最终形态；T18–T21 的真实实现必须遵守同一契约。
"""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import QObject, Signal

from shiguang.services.dto import ArchiveInput, TodaySummary, TodoItem


class TaskServiceInterface(QObject):
    """代办服务接口（Mock 与真实实现的公共基类）。

    `changed` 信号：任何数据变更（创建/编辑/删除/归档/延期）后发射，
    UI 各页面订阅它做整体刷新。
    """

    changed = Signal()

    # ----- 查询 -----
    def list_today(self, day: date) -> list[TodoItem]:
        """指定日期的待办代办（pending，按计划日期升序）。"""
        raise NotImplementedError

    def list_pending(self) -> list[TodoItem]:
        """全部待办代办（按计划日期升序）。"""
        raise NotImplementedError

    def list_overdue(self) -> list[TodoItem]:
        """全部逾期代办（pending 且 date < 今天）。"""
        raise NotImplementedError

    def list_archived(self, day: date | None = None) -> list[TodoItem]:
        """已归档代办；day 为空时返回全部（按归档时间倒序）。"""
        raise NotImplementedError

    def list_todo_dates(self) -> set[date]:
        """有待办的日期集合（DateBar 圆点用）。"""
        raise NotImplementedError

    def today_summary(self, day: date) -> TodaySummary:
        """今日概览：总数（待办+今日已归档）与已归档数。"""
        raise NotImplementedError

    # ----- 变更 -----
    def create_todo(
        self,
        name: str,
        standard: str,
        description: str = "",
        day: date | None = None,
        repeat: str = "none",
        end_date: date | None = None,
        priority: str = "gray",
        delay_policy: str = "default",
    ) -> TodoItem:
        """创建代办。name / standard 必填（去空白后非空），否则抛 ValueError。

        repeat = "none"：day 为计划日期，生成一条记录。
        repeat = "daily" / "weekly" / "monthly"：day 为开始日期，end_date 必填；
        按 [day, end_date] 创建时一次性展开为多条独立记录（共享同一系列标识），
        返回首条记录；end_date 早于 day 或展开条数超上限时抛 ValueError。
        """
        raise NotImplementedError

    def update_todo(self, task_id: int, **fields) -> TodoItem:
        """编辑代办（仅 pending）；已归档抛 ValueError。"""
        raise NotImplementedError

    def delete_todo(self, task_id: int) -> None:
        """删除代办（仅 pending）；已归档抛 ValueError。"""
        raise NotImplementedError

    def archive(self, task_id: int, data: ArchiveInput) -> TodoItem:
        """归档代办。score ∈ [1,5]、duration > 0，否则抛 ValueError。"""
        raise NotImplementedError
