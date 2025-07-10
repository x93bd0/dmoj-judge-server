from .config import (
    BaseConfig,
    ProblemConfig,
    TestCaseConfig,
    BatchedTestCaseConfig,
)
from .cptbox.utils import MmapableIO, MemoryIO
from .errors import InvalidInitException
from dataclasses import dataclass
from io import BufferedReader
from typing import Any
import zipfile
import shutil
import os


class ProblemDataManager:
    root_path: str
    archive: zipfile.ZipFile | None

    def __init__(self, root_path: str) -> None:
        self.root_path = root_path
        self.archive = None

    def open(self, path: str) -> BufferedReader:
        try:
            return open(os.path.join(self.root_path, path), "rb")
        except IOError:
            raise KeyError(
                'File "%s" could not be found in "%s"' % (path, self.root_path)
            )

    def open_fd(self, path: str, normalize: bool = False) -> MmapableIO:
        memory = MemoryIO()
        with self.open(path) as f:
            if normalize:
                raise NotImplementedError("open_fd(..., normalize = True)")
            else:
                shutil.copyfileobj(f, memory)
        memory.seal()
        return memory

    def __getitem__(self, key: str) -> bytes:
        with self.open(key) as f:
            return f.read()

    def __del__(self):
        # FIXME: Doesn't this happen implicitly?
        if self.archive:
            self.archive.close()


class Problem:
    id: str
    time_limit: float
    memory_limit: int
    # TODO: unpack and toss
    meta: dict[str, Any]

    config: ProblemConfig
    data_manager: ProblemDataManager

    pretests_only: bool
    _batch_counter: int
    _testcase_counter: int

    def __init__(
        self,
        id: str,
        time_limit: float,
        memory_limit: int,
        meta: dict[str, Any],
        config: ProblemConfig,
        data_manager: ProblemDataManager,
    ) -> None:
        self.id = id
        self.time_limit = time_limit
        self.memory_limit = memory_limit
        self.meta = meta
        self.config = config

        self._batch_counter = 0
        self._testcase_counter = 0

        self.pretests_only = self.meta.get("pretests_only", False)
        if not self._resolve_testcases():
            raise InvalidInitException("Problem `%s` has no testcases" % (id,))

    # TODO: typing
    def _resolve_testcases(self) -> list[dict[str, Any]]:
        test_cases = self.config.test_cases
        if test_cases is not None and isinstance(test_cases, list):
            return test_cases

        # FIXME
        raise NotImplementedError("Can't guess the testcase name format, yet!")

    def _load_testcases(
        self, case_configs: list[dict[str, Any]], batch_number: int = 0
    ) -> list["BaseTestCase"]:
        cases: list[BaseTestCase] = []
        for case_config in case_configs:
            if "batched" in case_config:
                config: BatchedTestCaseConfig = BatchedTestCaseConfig(
                    **case_config
                )
                self._batch_counter += 1

                sub_cases: list[BaseTestCase] = self._load_testcases(
                    config.batched
                )
                # TODO: Consider moving to __post_init__
                if any(
                    isinstance(sub_case, BatchedTestCase)
                    for sub_case in sub_cases
                ):
                    raise InvalidInitException("Batches can't be nested")

                if any(
                    dep >= self._batch_counter for dep in config.dependencies
                ):
                    raise InvalidInitException(
                        "Dependencies depends on non-earlier batch"
                    )

                if any(dep < 1 for dep in config.dependencies):
                    raise InvalidInitException(
                        "Dependencies must be positive integers"
                    )

                cases.append(
                    BatchedTestCase(
                        config,
                        config.points,
                        self,
                        self._batch_counter,
                        sub_cases,
                        config.dependencies,
                    )
                )
            else:
                if "in" in case_config:
                    case_config["_in"] = case_config.pop("in")
                config: TestCaseConfig = TestCaseConfig(**case_config)
                cases.append(
                    TestCase(
                        config,
                        config.points,
                        self,
                        self._testcase_counter,
                        batch_number,
                        config.output_prefix_length,
                        config.has_binary_data,
                    )
                )

                self._testcase_counter += 1
        return cases

    def cases(self) -> list["BaseTestCase"]:
        pretest_test_cases = self.config.pretest_test_cases
        if self.pretests_only and pretest_test_cases:
            return self._load_testcases(pretest_test_cases)

        test_cases = self._load_testcases(self.config.test_cases)
        if pretest_test_cases:
            pretest_test_cases = self._load_testcases(pretest_test_cases)
            # FIXME: Didn't implemented pretest short-circuit. Left for later.
            test_cases = pretest_test_cases + test_cases
        return test_cases

    @property
    def grader_class(self) -> Any:
        raise NotImplementedError("Problem.grader_class")

    def __repr__(self) -> str:
        return (
            "Problem("
            + f'id="{self.id}", '
            + f"time_limit={self.time_limit}, "
            + f"memory_limit={self.memory_limit}, "
            + f"pretests_only={self.pretests_only}, ...)"
        )


@dataclass
class BaseTestCase:
    # FIXME: What type does this take?
    config: dict[str, Any] | BaseConfig
    points: int
    # TODO: Maybe there's a way to remove this circular dependency without
    #         hurting performance?
    problem: Problem


@dataclass
class BatchedTestCase(BaseTestCase):
    batch_no: int
    cases: list[BaseTestCase]
    # TODO: typing
    dependencies: list[int]

    def __repr__(self) -> str:
        return f"BatchedTestCase(cases={self.cases})"


@dataclass
class TestCase(BaseTestCase):
    position: int
    batch: int
    output_prefix_length: int
    has_binary_data: bool

    def __repr__(self) -> str:
        return (
            "TestCase("
            + f'in="{self.config._in}", '
            + f'out="{self.config.out}", '
            + f"points={self.config.points})"
        )
