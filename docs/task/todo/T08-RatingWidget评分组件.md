# T08 RatingWidget 评分组件

- **所属阶段**：二 · UI 实现
- **前置任务**：T07
- **类型**：feat

## 任务目标

按 UI 设计文档 §5.3 / §4.4.3 实现星级评分组件。**本任务只做组件与预览验证，弹窗接线属 T13。**

## 任务内容

1. `ui/widgets/rating_widget.py`：
   - 5 颗星，支持 28px（归档弹窗）/ 20px（卡片展示）两种尺寸
   - 颜色：选中 `--star` (#FBBF24)，未选中 `--star-empty` (#D1D5DB)
   - 交互：hover 预览（悬停星及左侧全填充、放大 1.1 倍）、点击确定、点击回弹 0.9→1.0（§7.4）
   - 只读模式（已归档卡片展示用）
2. 评分标签（§4.4.3）：选中后下方显示对应文案与渐变颜色——
   1星"⭐ 还需努力"（偏 `--danger`）→ 5星"⭐ 完美达成"（偏 `--success`），标签开关可控（卡片场景不需要）
3. 组件接口：`set_score(n)` / `score()` / `set_read_only(bool)`，信号 `score_changed(int)`
4. 临时预览页验证两种尺寸与交互

## 涉及文件

- `src/shiguang/ui/widgets/rating_widget.py`（新建）
- `src/shiguang/ui/pages/dev_preview_page.py`（修改）

## 验收标准

- [ ] hover/点击/回弹动效符合 §7.4
- [ ] 五档标签文案与颜色正确
- [ ] 只读模式不可交互

## 备注

- 星星用 SVG 或 QPainter 自绘（Unicode ⭐ 渲染依赖系统字体，不推荐）。
