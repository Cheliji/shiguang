# T07 DateBar 周日期栏组件

- **所属阶段**：二 · UI 实现
- **前置任务**：T06
- **类型**：feat

## 任务目标

按 UI 设计文档 §4.1.3 / §5.2 实现 `DateBar` 周日期栏组件。**本任务只做组件与预览验证，页面接线属 T09。**

## 任务内容

1. `ui/widgets/date_bar.py`：
   - 白色卡片容器（圆角 12px、shadow-sm、内边距 12px 16px，高约 72px）
   - 左右箭头（24px 圆形按钮）切换上一周/下一周
   - 7 个日期项等分：星期文字（12px secondary）+ 日期数字（14px primary）
   - 选中态：`--primary` 背景 + 白字；有待办日期底部 4px 圆点（选中时白色，未选中主色）；悬停 `--bg-secondary` 背景 150ms 过渡
2. 组件接口：`set_week(anchor_date)`、`set_todo_dates(dates)`（控制圆点）、信号 `date_selected(date)`
3. 初始定位本周、选中今天
4. 临时预览页验证：前后翻周、选中切换、假数据圆点

## 涉及文件

- `src/shiguang/ui/widgets/date_bar.py`（新建）
- `src/shiguang/ui/pages/dev_preview_page.py`（修改）

## 验收标准

- [ ] 翻周、选中、圆点、悬停四交互正常
- [ ] 视觉与 §4.1.3 规格及原型一致
- [ ] 跨年/跨月翻周日期计算正确（单测或预览手工验证）

## 备注

- 周起始为周一（§4.1.3 示例）；日期计算用标准库 `datetime`，逻辑抽纯函数便于测试。
