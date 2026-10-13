# T22 启动流程整合与 Mock 下线

- **所属阶段**：三 · 数据层落地
- **前置任务**：T21
- **类型**：feat

## 任务目标

完成启动序列与跨天自动刷新，默认真实服务运行，Mock 仅保留测试/演示用途。**代办模块收官任务。**

## 任务内容

1. `app.py` 启动序列：
   ```
   QApplication → 定位数据目录 → upgrade_head()
   → InstanceGenerator.generate(today)
   → DelayService.scan(today)
   → 显示 MainWindow
   ```
   启动耗时给出 SplashScreen 加载反馈
2. 跨天定时器：`QTimer` 每 60s 检查日期，跨天后重跑 generate + scan 并发射 `changed`
3. 窗口激活事件补充一次日期检查（覆盖系统休眠场景）
4. `USE_MOCK` 默认 `false`；Mock 实现保留
5. 集成测试 `tests/test_startup.py`：fake 日期下启动序列端到端（模板生成实例 + auto 延期生效）
6. 全量回归：pytest 全过 + ruff 通过 + 手工 checklist：
   - 昨日创建"每日"模板 → 今日启动出现新实例
   - 逾期 auto 代办启动后顺延且 delay_count+1
   - 归档数据重启后持久
   - DateBar 圆点、概览卡片、表情与真实数据一致
7. 更新 `docs/task/task.md`：模块一全部标记 ✅

## 涉及文件

- `src/shiguang/app.py`、`main.py`、`config.py`（修改）
- `tests/test_startup.py`（新建）

## 验收标准

- [ ] 启动序列集成测试通过
- [ ] 跨天定时器单测通过
- [ ] 手工 checklist 四项全过
- [ ] 全量测试 + ruff 通过；task.md 模块一全部 ✅

## 备注

- 完成后拆解模块二（每日日记），同样遵循"原型（UI 设计文档 §4.5）→ UI(Mock) → 数据"顺序，并接线今日页日记卡片。
