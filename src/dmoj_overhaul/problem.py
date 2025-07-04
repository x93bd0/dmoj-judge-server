from typing import Any
from dataclasses import dataclass
from .config import ProblemConfig


class Problem:
    id: str
    time_limit: float
    memory_limit: int
    meta: dict[str, Any]

    root_dir: str
    config: ProblemConfig


@dataclass
class BaseTestCase:
    # FIXME: What type does this take?
    config: Any
    points: int
    # TODO: Maybe there's a way to remove this circular dependency without
    #         hurting performance?
    problem: "Problem"


@dataclass
class BatchedTestCase(BaseTestCase):
    batch_no: int


@dataclass
class TestCase(BaseTestCase):
    batch: int
    output_prefix_length: int
    has_binary_data: bool
