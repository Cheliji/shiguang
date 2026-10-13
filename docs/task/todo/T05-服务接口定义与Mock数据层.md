# T05 服务接口定义与 Mock 数据层

- **所属阶段**：二 · UI 实现
- **前置任务**：T04
- **类型**：feat

## 任务目标

定义阶段二 UI 与阶段三真实实现共用的**服务接口契约（Protocol + DTO）**，并提供内存 Mock 实现。UI 层从此只依赖接口与假数据开发，不碰数据库。

## 任务内容

1. `services/dto.py`：UI 与服务层之间的数据传输对象
   - `TodoItem`：id、name、description、standard、date、repeat、delay_policy、delay_count、status、is_overdue（计算属性或字段）
   - `ArchiveInput`：duration、score、summary
2. `services/interfaces.py`：`TaskService` Protocol
   - `list_today() / list_pending() / list_overdue() / list_archived(date=None)`
   - `create_todo(...) / update_todo(...) / delete_todo(...)`
   - `archive(task_id, ArchiveInput)`
   - `changed` 信号（数据变更通知，Mock 也要发射）
3. `services/mock/mock_task_service.py`：内存列表实现，预置一组假数据（含：普通今日代办、带完成标准的代办、逾期代办、每日重复代办、已归档代办），覆盖列表与弹窗的各种展示场景
4. `services/__init__.py` 或 `app.py` 提供 `get_task_service()` 工厂（读 `USE_MOCK` 开关，当前恒为 Mock）
5. 单元测试：Mock 实现的增删改与归档行为符合接口约定（这份测试在阶段三可直接复用到真实实现上）

## 涉及文件

- `src/shiguang/services/dto.py`、`interfaces.py`（新建）
- `src/shiguang/services/mock/mock_task_service.py`（新建）
- `tests/test_task_service_contract.py`（新建：针对接口的契约测试）

## 验收标准

- [ ] 接口方法签名覆盖 T07–T12 全部 UI 需求（含归档、重复字段、延期字段）
- [ ] Mock 假数据覆盖上述 5 类场景
- [ ] 契约测试通过；UI 层 import 检查：ui/ 下无 SQLAlchemy/models 引用

## 备注

- 接口设计以真实业务为准（签名即最终形态），Mock 只做最简内存模拟；重复实例生成、延期扫描等复杂规则不在 Mock 中实现（Mock 里"每日重复代办"直接预置一条今日数据即可）。
