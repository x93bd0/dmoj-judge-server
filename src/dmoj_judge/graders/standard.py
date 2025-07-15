from ..executors import BaseExecutor
from ..types import TestCase, Result
from .base import BaseGrader


class StandardGrader(BaseGrader):
    def grade(self, case: TestCase) -> Result:
        result = Result(case)

        error = None

        assert self._current_process is not None
        self.executor.populate_result(error, result, self._current_process)

        check = self.check_result(case, result)

        # if not isinstance(check, CheckerResult):

    def _create_executor(self) -> BaseExecutor:
        return self.executor_type(
            self.problem.id,
            self.source,
            hints=self.problem.config.hints or [],
            unbuffered=self.problem.config.unbuffered,
        )
