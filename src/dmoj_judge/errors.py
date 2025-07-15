from typing import Self


class JudgeException(Exception):
    @classmethod
    def from_exception(cls, e: Exception) -> Self:
        return cls(str(e))


class InvalidConfigurationError(JudgeException):
    pass


class ProblemManagerException(JudgeException):
    pass


class InvalidInitError(ProblemManagerException):
    pass


class GraderManagerException(JudgeException):
    pass


class InvalidGraderNameError(GraderManagerException):
    def __init__(self, name: str):
        super().__init__(f"There is no loaded `Grader` named `{name}`")


class ExecutorManagerException(JudgeException):
    pass


class InvalidExecutorNameError(JudgeException):
    def __init__(self, name: str):
        super().__init__(f"There is no loaded `Executor` named `{name}`")


class InternalError(JudgeException):
    pass
