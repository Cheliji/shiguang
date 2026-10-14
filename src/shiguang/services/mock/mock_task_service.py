"""内存 Mock 代办服务（阶段二 UI 开发用）。

简化规则（与真实实现的差异，真实规则见 T19/T20）：
- 每日/每周/每月重复：不做实例生成，创建时直接以今天为计划日期落一条数据，
  卡片带重复标签即可满足 UI 演示；
- 不做自动延期扫描，逾期数据为预置假数据；
- 数据存内存，重启即失。
"""

from datetime import date, datetime, timedelta

from shiguang.services.dto import (
    DELAY_AUTO,
    REPEAT_DAILY,
    STATUS_ARCHIVED,
    STATUS_PENDING,
    ArchiveInput,
    TodaySummary,
    TodoItem,
)
from shiguang.services.interfaces import TaskServiceInterface


def _validate_create(name: str, standard: str) -> None:
    if not name.strip():
        raise ValueError("代办名称不能为空")
    if not standard.strip():
        raise ValueError("完成标准不能为空")


def _validate_archive(data: ArchiveInput) -> None:
    if not 1 <= data.score <= 5:
        raise ValueError("评分必须为 1-5")
    if data.duration <= 0:
        raise ValueError("用时必须大于 0 分钟")


class MockTaskService(TaskServiceInterface):
    """内存版代办服务。"""

    def __init__(self, with_seed: bool = True) -> None:
        super().__init__()
        self._items: list[TodoItem] = []
        self._next_id = 1
        if with_seed:
            self._seed()

    # ---------- 假数据 ----------
    def _seed(self) -> None:
        today = date.today()
        yesterday = today - timedelta(days=1)

        def s(**kwargs) -> TodoItem:
            kwargs.setdefault("id", 0)
            return TodoItem(**kwargs)

        seeds = [
            # 普通今日代办
            s(
                name="整理电脑桌面文件",
                standard="收件箱清空，桌面仅保留本周项目文件夹",
                description="顺手把下载目录也清理一下",
                date=today,
            ),
            # 带完成标准 + 描述的今日代办
            s(
                name="阅读《设计心理学》 chapter 3",
                standard="写 3 条读书笔记，能复述核心观点",
                description="准备读书笔记，用于周末分享",
                date=today,
            ),
            # 每日重复代办（含 end_date 示例）
            s(
                name="背 20 个英语单词",
                standard="在 App 内完成今日词卡，正确率 ≥ 80%",
                date=today,
                end_date=today + timedelta(days=30),
                repeat=REPEAT_DAILY,
            ),
            # 逾期代办（自动延期过一次）
            s(
                name="给手机相册分类",
                standard="相册按年份建文件夹，废片删除",
                date=yesterday,
                delay_policy=DELAY_AUTO,
                delay_count=1,
            ),
            # 已归档代办（今天完成）
            s(
                name="晨跑 5 公里",
                standard="配速低于 6:00，跑后拉伸",
                date=today,
                status=STATUS_ARCHIVED,
                score=4,
                duration=30,
                summary="今天状态不错，最后一公里提速了",
                archived_at=datetime.combine(today, datetime.min.time()).replace(hour=7, minute=30),
            ),
            # 已归档代办（昨天完成）
            s(
                name="回复合作方邮件",
                standard="三个问题全部答复，附件齐全",
                date=yesterday,
                status=STATUS_ARCHIVED,
                score=3,
                duration=15,
                summary="",
                archived_at=datetime.combine(yesterday, datetime.min.time()).replace(
                    hour=18, minute=5
                ),
            ),
        ]
        for item in seeds:
            self._append(item)

    def _append(self, item: TodoItem) -> TodoItem:
        item.id = self._next_id
        self._next_id += 1
        self._items.append(item)
        return item

    def _get(self, task_id: int) -> TodoItem:
        for item in self._items:
            if item.id == task_id:
                return item
        raise ValueError(f"代办不存在: {task_id}")

    # ---------- 查询 ----------
    def list_today(self, day: date) -> list[TodoItem]:
        return sorted(
            (i for i in self._items if i.status == STATUS_PENDING and i.date == day),
            key=lambda i: i.id,
        )

    def list_pending(self) -> list[TodoItem]:
        return sorted(
            (i for i in self._items if i.status == STATUS_PENDING),
            key=lambda i: (i.date or date.max, i.id),
        )

    def list_overdue(self) -> list[TodoItem]:
        return [i for i in self.list_pending() if i.is_overdue()]

    def list_archived(self, day: date | None = None) -> list[TodoItem]:
        items = [i for i in self._items if i.status == STATUS_ARCHIVED]
        if day is not None:
            items = [i for i in items if i.archived_at and i.archived_at.date() == day]
        return sorted(items, key=lambda i: i.archived_at or datetime.min, reverse=True)

    def list_todo_dates(self) -> set[date]:
        return {i.date for i in self._items if i.status == STATUS_PENDING and i.date}

    def today_summary(self, day: date) -> TodaySummary:
        pending = len(self.list_today(day))
        archived_today = len(self.list_archived(day))
        return TodaySummary(total=pending + archived_today, archived=archived_today)

    # ---------- 变更 ----------
    def create_todo(
        self,
        name: str,
        standard: str,
        description: str = "",
        day: date | None = None,
        repeat: str = "none",
        end_date: date | None = None,
        weekday: int | None = None,
        month_day: int | None = None,
        delay_policy: str = "default",
    ) -> TodoItem:
        _validate_create(name, standard)
        item = TodoItem(
            id=0,
            name=name.strip(),
            standard=standard.strip(),
            description=description.strip(),
            date=day,
            repeat=repeat,
            end_date=end_date,
            weekday=weekday,
            month_day=month_day,
            delay_policy=delay_policy,
        )
        self._append(item)
        self.changed.emit()
        return item

    def update_todo(self, task_id: int, **fields) -> TodoItem:
        item = self._get(task_id)
        if item.status == STATUS_ARCHIVED:
            raise ValueError("已归档代办不可编辑")
        if "name" in fields:
            if not str(fields["name"]).strip():
                raise ValueError("代办名称不能为空")
            item.name = str(fields["name"]).strip()
        if "standard" in fields:
            if not str(fields["standard"]).strip():
                raise ValueError("完成标准不能为空")
            item.standard = str(fields["standard"]).strip()
        for key in (
            "description",
            "date",
            "repeat",
            "end_date",
            "weekday",
            "month_day",
            "delay_policy",
        ):
            if key in fields:
                setattr(item, key, fields[key])
        self.changed.emit()
        return item

    def delete_todo(self, task_id: int) -> None:
        item = self._get(task_id)
        if item.status == STATUS_ARCHIVED:
            raise ValueError("已归档代办不可删除")
        self._items.remove(item)
        self.changed.emit()

    def archive(self, task_id: int, data: ArchiveInput) -> TodoItem:
        item = self._get(task_id)
        if item.status == STATUS_ARCHIVED:
            raise ValueError("代办已归档")
        _validate_archive(data)
        item.status = STATUS_ARCHIVED
        item.score = data.score
        item.duration = data.duration
        item.summary = data.summary.strip() or None
        item.archived_at = datetime.now()
        self.changed.emit()
        return item
