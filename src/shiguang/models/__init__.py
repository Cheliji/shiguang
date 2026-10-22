"""ORM 模型包。

import 本包即注册全部模型（Alembic autogenerate 依赖完整的 metadata）。
"""

from shiguang.models.base import Base
from shiguang.models.task import Task

__all__ = ["Base", "Task"]
