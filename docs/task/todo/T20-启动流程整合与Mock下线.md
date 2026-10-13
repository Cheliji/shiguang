# T20 启动流程整合与 Mock 下线

- **所属阶段**：三 · 数据层落地
- **前置任务**：T19
- **类型**：feat

## 任务目标

完成启动序列与跨天自动刷新，默认以真实服务运行，Mock 仅保留在测试/演示用途。**代办模块收官任务。**

## 任务内容

1. `app.py` 启动序列：
   ```
   QApplication → 定位数据目录 → upgrade_head()
   → InstanceGenerator.generate(today)
   → DelayService.scan(today)
   → 显示 MainWindow
   ```
   启动耗时操作给出简单加载反馈（SplashScreen）
2. 跨天定时器：`QTimer` 每 60s 检查日期，跨天后重跑 generate + scan 并发射 `changed`
3. 窗口激活事件补充一次日期检查（覆盖系统休眠场景）
4. `USE_MOCK` 默认置为 `false`；Mock 实现保留（测试与原型演示用）
5. 集成测试：启动序列在测试库上端到端验证（fake 日期：模板生成实例 + auto 延期生效）
6. 全量回归：pytest 全过 + ruff 通过 + 手工 checklist：
   - 昨日创建"每日"模板 → 今日启动出现新实例
   - 逾期 auto 代办启动后顺延且 delay_count+1
   - 归档数据重启后持久
7. 更新 `docs/task/task.md`：模块一全部标记 ✅

## 涉及文件

- `src/shiguang/app.py`、`main.py`（修改）
- `src/shiguang/config.py`（修改：USE_MOCK 默认 false）
- `tests/test_startup.py`（新建）

## 验收标准

- [ ] 启动序列集成测试通过
- [ ] 跨天定时器逻辑单测通过
- [ ] 手工 checklist 三项全过
- [ ] 全量测试 + ruff 通过；task.md 模块一全部 ✅

## 备注

- 完成后开始拆解模块二（每日日记），同样遵循"原型 → UI(Mock) → 数据"的顺序；日记原型可复用 T01 的框架风格。
