# T05 服务接口定义与 Mock 数据层

- **所属阶段**：二 · UI 实现
- **前置任务**：T04
- **类型**：feat

## 任务目标

定义阶段二 UI 与阶段三真实实现共用的**服务接口契约（Protocol + DTO）**，并提供内存 Mock 实现。UI 层从此只依赖接口与假数据开发，不碰数据库。

## 任务内容

1. `services/dto.py`：
   - `TodoItem`：id、name、description、standard、date、repeat、delay_policy、delay_count、status、is_overdue；已归档项附带 score / duration / summary / archived_at
   - `ArchiveInput`：duration（必填）、score（必填，1–5）、summary（**可选**，对齐产品文档 v0.3）
   - `TodaySummary`：今日总数 / 已归档数 / 完成率（供今日页概览卡片）
2. `services/interfaces.py`：`TaskService` Protocol
   - `list_today(date)` / `list_pending()` / `list_overdue()` / `list_archived(date=None)` / `today_summary(date)`
   - `create_todo(...)` / `update_todo(...)` / `delete_todo(...)`
   - `archive(task_id, ArchiveInput)`
   - `changed` 信号（Mock 也要发射）
3. `services/mock/mock_task_service.py`：内存实现，预置假数据覆盖：普通今日代办、带完成标准的代办、逾期代办（含 delay_count>0）、每日重复代办、已归档代办（带评分/用时/总结）
4. `get_task_service()` 工厂（读 `USE_MOCK` 开关，当前恒为 Mock）
5. 契约测试：增删改、归档（总结可空）、`today_summary` 计数——**该测试阶段三直接复用到真实实现**

## 涉及文件

- `src/shiguang/services/dto.py`、`interfaces.py`、`mock/mock_task_service.py`（新建）
- `tests/test_task_service_contract.py`（新建）

## 验收标准

- [ ] 接口方法覆盖 T06–T14 全部 UI 需求
- [ ] Mock 假数据覆盖上述 5 类场景
- [ ] 契约测试通过；ui/ 下无 SQLAlchemy/models 引用

## 备注

- 接口签名即最终形态。Mock 只做最简内存模拟：重复/延期规则不实现（"每日"代办直接预置一条今日数据），真实规则属 T19/T20。
