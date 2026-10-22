"""重复代办日期展开纯函数测试（T24 引入，T19 真实服务复用同一函数）。

断言示例取自产品文档 v0.5 §6 / 任务书 T19、T24。
"""

from datetime import date, timedelta

import pytest

from shiguang.domain.rules import MAX_EXPAND_COUNT, expand_dates


# ---------- 每日 ----------
def test_daily_includes_both_ends():
    dates = expand_dates("daily", date(2026, 10, 22), date(2026, 11, 1))
    assert len(dates) == 11
    assert dates[0] == date(2026, 10, 22)
    assert dates[-1] == date(2026, 11, 1)
    # 逐日连续
    assert all(dates[i + 1] - dates[i] == timedelta(days=1) for i in range(len(dates) - 1))


def test_daily_single_day():
    assert expand_dates("daily", date(2026, 10, 22), date(2026, 10, 22)) == [date(2026, 10, 22)]


# ---------- 每周 ----------
def test_weekly_steps_7_days_from_start():
    dates = expand_dates("weekly", date(2026, 10, 22), date(2026, 11, 1))
    assert dates == [date(2026, 10, 22), date(2026, 10, 29)]


def test_weekly_never_exceeds_end():
    dates = expand_dates("weekly", date(2026, 10, 22), date(2026, 11, 5))
    # 10-22、10-29、11-05；下一条 11-12 超出结束日期
    assert dates == [date(2026, 10, 22), date(2026, 10, 29), date(2026, 11, 5)]


# ---------- 每月 ----------
def test_monthly_same_day_each_month():
    dates = expand_dates("monthly", date(2026, 10, 22), date(2027, 11, 1))
    assert len(dates) == 13
    assert dates[0] == date(2026, 10, 22)
    assert dates[-1] == date(2027, 10, 22)  # 2027-11-22 超出结束日期
    assert all(d.day == 22 for d in dates)


def test_monthly_skips_month_without_the_day():
    # 1 月 31 日起每月重复：2 月、4 月没有 31 日，跳过
    dates = expand_dates("monthly", date(2026, 1, 31), date(2026, 5, 31))
    assert dates == [date(2026, 1, 31), date(2026, 3, 31), date(2026, 5, 31)]


def test_monthly_leap_day_skips_common_years():
    # 2 月 29 日起每月重复：平年 2 月无 29 日，该月跳过
    dates = expand_dates("monthly", date(2024, 2, 29), date(2025, 4, 30))
    assert date(2024, 2, 29) in dates
    assert date(2025, 3, 29) in dates
    assert all(not (d.year == 2025 and d.month == 2) for d in dates)


# ---------- 边界 ----------
def test_end_before_start_raises():
    with pytest.raises(ValueError, match="结束日期不能早于开始日期"):
        expand_dates("daily", date(2026, 11, 1), date(2026, 10, 22))


def test_over_limit_raises():
    # 每日两年 = 700+ 条，超过 400 上限
    with pytest.raises(ValueError, match="超过上限"):
        expand_dates("daily", date(2026, 1, 1), date(2028, 1, 1))


def test_exactly_at_limit_ok():
    end = date(2026, 1, 1) + timedelta(days=MAX_EXPAND_COUNT - 1)
    assert len(expand_dates("daily", date(2026, 1, 1), end)) == MAX_EXPAND_COUNT


def test_unknown_repeat_raises():
    with pytest.raises(ValueError):
        expand_dates("yearly", date(2026, 1, 1), date(2026, 2, 1))
