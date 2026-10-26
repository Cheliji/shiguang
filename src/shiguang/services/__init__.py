"""服务工厂：按 USE_MOCK 开关返回 Mock 或真实实现（T22 起默认真实实现）。

正常启动由 `app.bootstrap_services` 装配并经 `set_task_service` 注册；
本模块的懒加载分支（get_task_service）是未走启动序列时的兜底。
"""

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


def set_task_service(service: TaskServiceInterface) -> None:
    """注册外部装配好的服务实例（app 启动序列用）。"""
    global _task_service
    _task_service = service


def _build_real_service() -> TaskServiceInterface:
    """懒加载兜底：迁移到最新版（幂等）→ 真实服务。"""
    from shiguang.app import bootstrap_services

    services = bootstrap_services()
    assert services is not None  # USE_MOCK 分支不会走到这里
    return services[0]


def reset_task_service() -> None:
    """测试用：重置服务实例。"""
    global _task_service
    _task_service = None
