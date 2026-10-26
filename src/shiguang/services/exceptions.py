"""服务层异常体系（T18）。

三类业务错误均继承 ValueError，保持 T05 接口契约不变：
UI 现有的 `except ValueError` 与契约测试继续有效。
"""


class TaskServiceError(ValueError):
    """代办服务错误基类（同时是 ValueError，兼容 T05 契约）。"""


class ValidationError(TaskServiceError):
    """参数校验失败（名称为纯空白、完成标准为空、重复规则暂不支持等）。"""


class TaskNotFoundError(TaskServiceError):
    """任务不存在。"""


class TaskArchivedError(TaskServiceError):
    """对已归档记录的操作（编辑/删除/重复归档）。"""
