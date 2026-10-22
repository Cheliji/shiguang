"""UI 与服务层之间的数据传输对象（DTO）。

字段取值的合法枚举（T16 会在 domain/enums.py 正式定义，此处先用字符串约定）：
- repeat: "none" / "daily" / "weekly" / "monthly"
- delay_policy: "default" / "never" / "auto"
- status: "pending" / "archived"
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

# 重复周期
REPEAT_NONE = "none"
REPEAT_DAILY = "daily"
REPEAT_WEEKLY = "weekly"
REPEAT_MONTHLY = "monthly"
REPEAT_CHOICES = (REPEAT_NONE, REPEAT_DAILY, REPEAT_WEEKLY, REPEAT_MONTHLY)
REPEAT_LABELS = {
    REPEAT_NONE: "不重复",
    REPEAT_DAILY: "每日",
    REPEAT_WEEKLY: "每周",
    REPEAT_MONTHLY: "每月",
}

# 延期策略
DELAY_DEFAULT = "default"
DELAY_NEVER = "never"
DELAY_AUTO = "auto"
DELAY_CHOICES = (DELAY_DEFAULT, DELAY_NEVER, DELAY_AUTO)
DELAY_LABELS = {
    DELAY_DEFAULT: "默认（不延期）",
    DELAY_NEVER: "不延期",
    DELAY_AUTO: "自动延期",
}

# 状态
STATUS_PENDING = "pending"
STATUS_ARCHIVED = "archived"


@dataclass
class TodoItem:
    """代办条目（UI 展示用）。"""

    id: int
    name: str
    standard: str = ""
    description: str = ""
    date: date | None = None
    repeat: str = REPEAT_NONE  # 创建时选择的重复规则；repeat != none 的记录属某个重复系列
    series_id: str | None = None  # 同一次创建时展开生成的记录共享同一系列标识
    delay_policy: str = DELAY_DEFAULT
    delay_count: int = 0
    status: str = STATUS_PENDING
    # 归档信息（status == archived 时填充）
    score: int | None = None
    duration: int | None = None
    summary: str | None = None
    archived_at: datetime | None = None

    def is_overdue(self, today: date | None = None) -> bool:
        """待办且计划日期早于今天。"""
        today = today or date.today()
        return self.status == STATUS_PENDING and self.date is not None and self.date < today


@dataclass
class ArchiveInput:
    """归档输入（产品文档 v0.3：用时、评分必填；总结可选）。"""

    duration: int  # 分钟，> 0
    score: int  # 1-5
    summary: str = ""


@dataclass
class TodaySummary:
    """今日概览（今日页概览卡片用）。"""

    total: int = 0
    archived: int = 0

    @property
    def rate(self) -> float:
        """完成率 0.0-1.0。"""
        return self.archived / self.total if self.total else 0.0
