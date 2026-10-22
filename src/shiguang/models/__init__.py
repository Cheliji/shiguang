"""ORM 模型包。

import 本包即注册全部模型（Alembic autogenerate 依赖完整的 metadata）。
T16 起注册业务模型。
"""

from shiguang.models.base import Base

__all__ = ["Base"]
