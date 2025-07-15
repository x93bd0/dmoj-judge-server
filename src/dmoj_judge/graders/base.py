from ..executors import BaseExecutor, ExecutorManager
from ..types import Result, Problem, TestCase
from ..cptbox import TracedPopen
from abc import ABCMeta, abstractmethod


class BaseGrader(ABCMeta):
    source: bytes
    problem: Problem
    executor_type: type[BaseExecutor]
    executor: BaseExecutor
    _current_process: TracedPopen | None

    def __init__(
        self,
        execm: ExecutorManager,
        problem: Problem,
        language: str,
        source: bytes,
    ) -> None:
        self.source = source
        self.language = language
        self.problem = problem
        self.binary = self._create_executor()
        self._abort_requested = False
        self._current_process = None

    # TODO: TestCase or BaseTestCase?
    @abstractmethod
    def grade(self, case: TestCase) -> Result:
        raise NotImplementedError

    @abstractmethod
    def _create_executor(self) -> BaseExecutor:
        raise NotImplementedError

    def abort_grading(self) -> None:
        self._abort_requested = True
        if self._current_process:
            try:
                self._current_process.kill()
            except OSError:
                # TODO: Wait, it just returns? No logging?
                pass
