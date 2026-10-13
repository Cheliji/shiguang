# T06 TaskCard 代办卡片组件

- **所属阶段**：二 · UI 实现
- **前置任务**：T05
- **类型**：feat

## 任务目标

按 UI 设计文档 §5.1 实现 `TaskCard` 组件，支持全部状态变体。**本任务只做组件本身与临时预览页，不接页面。**

## 任务内容

1. `ui/widgets/task_card.py`，规格严格按 §5.1：
   - 结构：Checkbox（20px）+ 名称（15px Medium）+ 完成标准摘要（📋 前缀，单行省略）+ 元信息行（目标 Pill / 日期 / Badge）+ 右侧操作菜单（⋯：编辑/删除/归档）
   - Checkbox 交互：默认/悬停/选中/已归档只读（绿色）四态（§5.1.2），勾选动画 100ms（§7.4）
   - **点击 Checkbox = 发起归档**：发射 `archive_requested(task_id)`（弹窗接线属 T13，本任务仅发信号）
2. 状态变体（§5.1.3）：默认 / 悬停（translateY(-1px) + shadow-md）/ 已完成删除线 / 逾期（左侧 4px 红条 + `#FFF5F5` 背景）/ 逾期已延期（+ 橙色 Badge）/ 归档态（透明度 0.85 + 评分用时）
3. 组件接口：`set_data(TodoItem)`；信号：`archive_requested`、`edit_requested`、`delete_requested`
4. 临时预览页 `ui/pages/dev_preview_page.py`：用 Mock 数据平铺全部变体，挂载导航供比对（T14 后摘除）
5. 样式全部取自 `theme.py` 令牌

## 涉及文件

- `src/shiguang/ui/widgets/task_card.py`、`ui/pages/dev_preview_page.py`（新建）

## 验收标准

- [ ] §5.1.3 六种变体渲染正确，与原型并排比对一致
- [ ] 长名称/长标准截断不撑破布局
- [ ] Checkbox 点击发出正确 task_id 信号

## 备注

- 阴影在 Qt 中用 `QGraphicsDropShadowEffect`；悬停位移可用动画或省略位移仅变阴影（记录取舍到 UI 设计文档差异备注）。
