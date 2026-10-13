# T05 代办 CRUD 服务

- **所属阶段**：二 · 业务服务层
- **前置任务**：T04
- **类型**：feat

## 任务目标

提供代办的创建 / 编辑 / 删除服务方法（不含重复实例生成、不含归档），含输入校验。**本任务只处理 `repeat='none'` 的普通代办；重复模板的实例生成属于 T06。**

## 任务内容

1. `services/task_service.py`：
   - `create_todo(...)`：校验 name 非空（去空白）、date 合法；`repeat != 'none'` 时创建模板记录并调用占位接口（T06 填充，本次先只落模板）
   - `update_todo(task_id, ...)`：仅允许编辑 `pending` 状态任务；归档任务抛 `TaskArchivedError`
   - `delete_todo(task_id)`：已归档任务禁止删除
2. 定义服务层异常：`ValidationError`、`TaskNotFoundError`、`TaskArchivedError`。
3. 操作成功后发射信号 `task_changed`（用简单的 `QObject` 信号持有器，定义在 `services/signals.py`，服务方法调用其 `emit`；UI 任务 T10 才接线）。
4. 单元测试：正常路径 + 每条校验规则 + 异常路径。

## 涉及文件

- `src/shiguang/services/task_service.py`、`services/signals.py`、`services/exceptions.py`（新建）
- `tests/test_task_service.py`（新建）

## 验收标准

- [ ] 创建/编辑/删除的单测全部通过
- [ ] 编辑或删除已归档任务抛出 `TaskArchivedError`
- [ ] 空名称、非法日期抛出 `ValidationError`

## 备注

- 信号发射与业务解耦：signals 持有器全局单例，服务层只 import 使用，不知道 UI 存在。
