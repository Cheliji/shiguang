"""领域纯函数：重复代办日期展开、延期判断（不依赖任何外层，可 100% 单元测试）。

T24 引入 `expand_dates`：创建弹窗的条数预览与 Mock 数据层共用；
T19 真实服务创建重复代办时复用同一函数，保证三处规则完全一致。
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta

# 单次展开条数上限（产品文档 v0.5 §6：超出时提示用户缩短日期范围）
MAX_EXPAND_COUNT = 400


def expand_dates(repeat: str, start: date, end: date) -> list[date]:
    """把 [start, end] 按重复规则展开为计划日期列表（含首尾边界）。

    - daily：逐日一条（例：10-22 ~ 11-01 → 11 条）
    - weekly：从 start 起每 7 天一条，不超过 end（例：10-22 ~ 11-01 → 2 条）
    - monthly：从 start 起每月同一日号一条，不超过 end；
      该月无此日号（如 2 月 31 日、平年 2 月 29 日）则跳过该月
      （例：2026-10-22 ~ 2027-11-01 → 每月 22 日共 13 条）

    边界：end < start 或条数超过 MAX_EXPAND_COUNT 时抛 ValueError；
    首条恒为 start（结果不会为空）。
    """
    if end < start:
        raise ValueError("结束日期不能早于开始日期")

    dates: list[date] = []
    if repeat == "daily":
        dates = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    elif repeat == "weekly":
        day = start
        while day <= end:
            dates.append(day)
            day += timedelta(days=7)
    elif repeat == "monthly":
        year, month = start.year, start.month
        while (year, month) <= (end.year, end.month):
            if start.day <= monthrange(year, month)[1]:  # 该月有此日号
                day = date(year, month, start.day)
                if start <= day <= end:
                    dates.append(day)
            # 月份步进（跨年回绕）
            if month == 12:
                year, month = year + 1, 1
            else:
                month += 1
    else:
        raise ValueError(f"未知重复规则: {repeat}")

    if len(dates) > MAX_EXPAND_COUNT:
        raise ValueError(f"生成条数超过上限 {MAX_EXPAND_COUNT} 条，请缩短日期范围")
    return dates
