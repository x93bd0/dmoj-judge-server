from typing import Self


class JudgeException(Exception):
    @classmethod
    def from_exception(cls, e: Exception) -> Self:
        return cls(str(e))


class ProblemManagerException(JudgeException):
    pass


class InvalidInitException(ProblemManagerException):
    pass


class InternalError(JudgeException):
    pass
