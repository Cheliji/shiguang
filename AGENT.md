## 注意事项
- 每一次改动完成之后，都需要创建一个对应的 Git commit（注意不是 push 至远程仓库），以便后续追踪与回滚。

## UI 样式规则（PySide6 / QSS）

### 禁止对「容器」使用无选择器的 background

**反例（会产生 bug）：**
```python
container.setStyleSheet("background: #F3F4F6;")  # ❌ 无选择器
```

**原因**：QSS 规则会沿控件父子树向下级联。容器上无选择器的 `background` 会作用于所有后代，
导致每个 QLabel / 图标控件都被涂上一层祖先的背景色块（文字、图标背后出现与父容器背景冲突的色块）。
这与前端 CSS 中 `div { background }` 不影响 span 不同——Qt 的无选择器写法更接近 `* { background }`。

**正确做法**：容器背景必须用限定选择器，只作用于容器自身：
1. 自定义类选择器：`class TaskCard(QFrame)` → `TaskCard { background: ... }`（类名不匹配后代，天然安全）；
2. objectName 选择器：通用容器一律使用 `shiguang.ui.theme.set_container_bg(widget, name, color, radius)` 辅助函数。

**例外**：叶子控件（自身就是要显示底色的 Pill / Badge / 分割线 / 圆点，且无子控件）允许用无选择器写法。
另外，写类型选择器（如 `QFrame { ... }`）时注意它会匹配所有后代中的 QFrame 子类（含 QLabel），容器上同样应避免。

### 所有按钮/图标必须使用矢量图标库

**规则**：任何带图形的按钮或指示（如 ^ v 步进箭头、下拉箭头、关闭 ×、加减号等），一律使用
Feather/Lucide SVG（`resources/icons/` + `ui/icons.py` 的 `colored_icon` / `colored_pixmap`），
**禁止使用**：

1. Qt 原生风格绘制的子控件按钮（如 QSpinBox 的上下箭头、QComboBox 的原生下拉箭头）——点击区域小、渲染模糊、容易点了没反应；
2. 手画图标或用字符/Emoji 模拟按钮图标——精度缺失。

**替代方案**：

- 数字输入：用 `ui/widgets/form_fields.py` 的 `NumberField`（纯文本输入 + 右侧内嵌矢量图标，焦点下滚轮微调），不要用 QSpinBox；
- 下拉框：用 `ChevronComboBox`（隐藏原生 down-arrow，叠加 chevron-down 矢量图标）；
- 需要新图标时，从 Feather/Lucide 下载 SVG 放入 `resources/icons/`（MIT 许可，与现有图标同源）。