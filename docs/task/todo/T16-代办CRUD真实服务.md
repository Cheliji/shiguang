# T16 代办 CRUD 真实服务（替换 Mock）

- **所属阶段**：三 · 数据层落地
- **前置任务**：T15
- **类型**：feat

## 任务目标

实现 `TaskService` 的真实版本（SQLAlchemy 持久化），覆盖创建/编辑/删除/各列表查询，并通过开关让应用切换为真实实现。**重复实例生成（T17）、延期扫描（T18）、归档（T19）本任务不做——真实服务中这些方法先抛 `NotImplementedError`，应用仍可对不重复代办走真实库。**

## 任务内容

1. `services/task_service.py`：实现 `services/interfaces.py` 的 `TaskService` 协议
   - `create_todo`：校验 name 非空（去空白）、date 合法；`repeat != 'none'` 时创建模板记录（实例生成留 T17 接入）
   - `update_todo` / `delete_todo`：仅允许 `pending` 状态；已归档抛 `TaskArchivedError`
   - `list_today / list_pending / list_overdue / list_archived`：走仓储层，返回 DTO
2. `services/exceptions.py`：`ValidationError`、`TaskNotFoundError`、`TaskArchivedError`
3. `app.py` 装配：`USE_MOCK=false` 时注入真实服务；`archive` 暂不可用（UI 上给出"即将支持"提示或直接禁用，T19 恢复）
4. **复用 T05 契约测试**跑真实实现，并补充：校验规则、归档任务保护等异常路径单测
5. 手工回归：真实库下创建/编辑/删除不重复代办全流程

## 涉及文件

- `src/shiguang/services/task_service.py`、`services/exceptions.py`（新建）
- `src/shiguang/app.py`（修改：装配开关）
- `tests/test_task_service.py`（新建）+ 契约测试复用

## 验收标准

- [ ] T05 契约测试对真实实现全部通过
- [ ] 校验与异常路径单测通过
- [ ] 真实库下不重复代办 CRUD 全流程手工验证通过

## 备注

- 分步替换期间保证应用随时可启动：Mock/真实由 `USE_MOCK` 一键切换。
