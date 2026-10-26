"""服务工厂：按 USE_MOCK 开关返回 Mock 或真实实现（T18 接入真实实现）。"""

from shiguang import config
from shiguang.services.interfaces import TaskServiceInterface

_task_service: TaskServiceInterface | None = None


def get_task_service() -> TaskServiceInterface:
    """全局唯一代办服务实例。"""
    global _task_service
    if _task_service is None:
        if config.USE_MOCK:
            from shiguang.services.mock.mock_task_service import MockTaskService

            _task_service = MockTaskService()
        else:
            _task_service = _build_real_service()
    return _task_service


def _build_real_service() -> TaskServiceInterface:
    """真实实现：迁移到最新版（幂等）→ 建引擎 → 服务。

    完整启动序列（数据目录定位、跨天定时器等）由 T22 整合。
    """
    from shiguang.db.migration_runner import upgrade_head
    from shiguang.db.session import create_engine_for, session_factory_for
    from shiguang.services.task_service import TaskService

    upgrade_head()
    engine = create_engine_for(config.get_db_path())
    return TaskService(session_factory_for(engine))


def reset_task_service() -> None:
    """测试用：重置服务实例。"""
    global _task_service
    _task_service = None
