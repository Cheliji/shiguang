"""领域枚举（技术设计文档 §4.2）。

`StrEnum`：成员值即数据库存储的字符串，与 `services/dto.py`
的字符串常量保持一致；ORM 用 String 列存储（SQLite 无原生 ENUM）。
"""

from enum import StrEnum


class TaskKind(StrEnum):
    """任务种类（v1.0 目标模块启用 goal）。"""

    TODO = "todo"
    GOAL = "goal"


class Period(StrEnum):
    """任务周期粒度。"""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class Repeat(StrEnum):
    """重复周期。"""

    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class DelayPolicy(StrEnum):
    """逾期延期策略。"""

    DEFAULT = "default"  # 默认（不延期，逾期样式展示）
    NEVER = "never"  # 不延期
    AUTO = "auto"  # 自动延期到当天


class TaskStatus(StrEnum):
    """任务状态。"""

    PENDING = "pending"
    ARCHIVED = "archived"


class Priority(StrEnum):
    """重要程度五色标识（产品文档 v0.6）：红 > 橙 > 蓝 > 绿 > 灰。"""

    RED = "red"
    ORANGE = "orange"
    BLUE = "blue"
    GREEN = "green"
    GRAY = "gray"
