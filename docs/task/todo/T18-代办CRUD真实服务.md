# T18 代办 CRUD 真实服务（替换 Mock）

- **所属阶段**：三 · 数据层落地
- **前置任务**：T17
- **类型**：feat

## 任务目标

实现 `TaskService` 真实版本（SQLAlchemy 持久化）并切换注入。**实例生成（T19）、延期扫描（T20）、归档（T21）本任务不做——这些方法先抛 `NotImplementedError`，UI 归档入口临时禁用并提示。**

## 任务内容

1. `services/task_service.py`：实现 T05 接口
   - `create_todo`：校验 name 非空（去空白）、**完成标准非空（v0.3 必填）**、date 合法；`repeat != 'none'` 时创建模板（实例生成留 T19）
   - `update_todo` / `delete_todo`：仅 `pending`；已归档抛 `TaskArchivedError`
   - `list_today / list_pending / list_overdue / list_archived / today_summary`：走仓储返回 DTO
2. `services/exceptions.py`：`ValidationError`、`TaskNotFoundError`、`TaskArchivedError`
3. `app.py` 装配：`USE_MOCK=false` 注入真实服务；UI 归档入口临时禁用（T21 恢复）
4. **复用 T05 契约测试**跑真实实现 + 补充异常路径单测（含完成标准必填）
5. 手工回归：真实库下创建/编辑/删除不重复代办全流程，重启后数据持久

## 涉及文件

- `src/shiguang/services/task_service.py`、`services/exceptions.py`（新建）
- `src/shiguang/app.py`（修改：装配开关）
- `tests/test_task_service.py`（新建）+ 契约测试复用

## 验收标准

- [ ] T05 契约测试对真实实现全部通过
- [ ] 异常路径单测通过
- [ ] 真实库 CRUD 手工验证通过，重启持久

## 备注

- 分步替换期间 `USE_MOCK` 一键切回，保证应用随时可演示。
