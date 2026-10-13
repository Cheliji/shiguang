# T06 TaskCard 代办卡片组件

- **所属阶段**：二 · UI 实现
- **前置任务**：T05
- **类型**：feat

## 任务目标

对照原型实现 `TaskCard` 组件，支持待办/逾期/已归档三种视觉状态。**本任务只做组件本身与一个临时预览页，不接列表页。**

## 任务内容

1. `ui/widgets/task_card.py`：
   - 待办态：名称、描述摘要（单行省略）、完成标准图标（有标准时显示，悬停 tooltip 展示全文）、右侧"归档"按钮（不接逻辑，发信号即可）、重复标识（如"每日"小标签）
   - 逾期态：左侧红色竖条 + 日期红色文案 + "已自动延期 N 次"（delay_count>0 时）
   - 已归档态：置灰、隐藏操作按钮、显示星级（只读）与总结摘要
2. 组件接口：`set_data(TodoItem)`、`archive_clicked = Signal(int)`（task_id）
3. 临时预览页（`ui/pages/dev_preview_page.py`，仅开发期挂载）：用 Mock 假数据平铺展示三种状态的卡片，方便与原型比对
4. 样式按技术设计文档 §6 设计令牌（QSS 集中在 resources 或组件内统一定义）

## 涉及文件

- `src/shiguang/ui/widgets/task_card.py`（新建）
- `src/shiguang/ui/pages/dev_preview_page.py`（新建，临时）
- `src/shiguang/resources/styles.qss`（如需）

## 验收标准

- [ ] 三种状态卡片渲染正确，与原型并排比对一致
- [ ] 长名称/长描述截断正常不撑破布局
- [ ] 点击"归档"能发出携带 task_id 的信号（打印验证）

## 备注

- 预览页在 T07 完成后从导航摘除，文件保留供后续组件调试。
