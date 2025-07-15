from typing import Self


class JudgeException(Exception):
    @classmethod
    def from_exception(cls, e: Exception) -> Self:
        return cls(str(e))


class ProblemManagerException(JudgeException):
    pass


class InvalidInitError(ProblemManagerException):
    pass


class GraderManagerException(JudgeException):
    pass


class InvalidGraderNameError(GraderManagerException):
    def __init__(self, name: str):
        super().__init__(f"`{name}`")


class InternalError(JudgeException):
    pass
