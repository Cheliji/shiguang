"""初始版本（空）：建立迁移基线，确保库文件与 alembic_version 就绪。

Revision ID: 0001
Revises:
Create Date: 2026-10-21

"""

from __future__ import annotations

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
