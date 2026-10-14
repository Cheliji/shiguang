"""服务工厂：按 USE_MOCK 开关返回 Mock 或真实实现（真实实现 T18 接入）。"""

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
            # T18：替换为真实实现
            from shiguang.services.mock.mock_task_service import MockTaskService

            _task_service = MockTaskService()
    return _task_service


def reset_task_service() -> None:
    """测试用：重置服务实例。"""
    global _task_service
    _task_service = None
