from dataclasses import dataclass, field
from .enums import BuiltInGraders
from typing import Any
import logging


class BaseConfig:
    def load_dict(self, base: dict[str, Any]) -> None:
        for key, value in base.items():
            try:
                cls_value: Any | BaseConfig = getattr(self, key)
            except AttributeError:
                raise AttributeError(
                    f"Config class `{type(self).__name__}` doesn't allow the `{key}` field"
                )

            if isinstance(cls_value, BaseConfig) and isinstance(value, dict):
                cls_value.load_dict(value)
            else:
                setattr(self, key, value)


# TODO: Maybe refactor this as PerExecutorConfig rather than AllExecutorsConfig?
@dataclass
class ExecutorConfig(BaseConfig):
    selftest_time_limit: int = 10
    selftest_memory_limit: int = 131072
    generator_compile_time_limit: int = 30
    generator_time_limit: float = 20.0
    generator_memory_limit: int = 524288
    validator_compiler_time_limit: float = 30.0
    validator_time_limit: float = 20.0
    validator_memory_limit: int = 524288
    compiler_time_limit: float = 10.0
    compiler_size_limit: int = 131072
    compiler_output_character_limit: int = 65536
    compiled_binary_cache_dir: str | None = None
    compiled_binary_cache_size: int = 100
    runtime: dict[str, Any] = field(default_factory=dict)
    temp_directory: str = "/tmp/"
    submission_cpu_affinity: list[int] | None = None


# FIXME: This wasn't tested nor investigated enough, so I can't ensure every
#         ProblemConfig can fit this schema the way the original DMOJ devs
#         intended.
@dataclass
class ProblemConfig(BaseConfig):
    # TODO: Find a more "elegant" way of passing down the grader configuraiton
    archive: str | None = None
    grader: str = BuiltInGraders.STANDARD.value
    grader_config: dict[str, Any] = field(default_factory=dict)

    unbuffered: bool = False

    # TODO: Couldn't this be replaced by a more sophisticated test case logic?
    #        (dunno, just ideas)
    # TODO: typing
    pretest_test_cases: list[Any] | dict[str, Any] | None = None
    test_cases: list[Any] | dict[str, Any] | None = None

    # TODO: Should this belong here?
    hints: list[str] = field(default_factory=list)
    checker: str = "standard"

    wall_time_factor: int = 3
    output_prefix_length: int = 0
    output_limit_length: int = 25165824
    binary_data: bool = False
    short_circuit: bool = True
    # TODO: typing
    dependencies: list = field(default_factory=list)
    points: int = 1
    # TODO: typing
    symlinks: dict = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraderManagerConfig(BaseConfig):
    include_builtin: bool = True
    external: dict[str, str] = field(default_factory=dict)


@dataclass
class ExecutorManagerConfig(BaseConfig):
    include_builtin: bool = True
    builtin_whitelist: list[str] | None = None
    builtin_blacklist: list[str] | None = None
    external: dict[str, str] = field(default_factory=dict)


@dataclass
class BatchedTestCaseConfig(BaseConfig):
    batched: list[dict[str, Any]]
    points: int = 0
    dependencies: list = field(default_factory=list)


@dataclass
class TestCaseConfig(BaseConfig):
    _in: str | None = None
    out: str | None = None
    points: int = 0
    output_prefix_length: int = 0
    has_binary_data: bool = False


# TODO: Consider adding a root logger property for doing root_logger.getChild('pkg')
# TODO: Implement type checker
# TODO: Add API flags
@dataclass
class Config(BaseConfig):
    server_host: str
    server_port: int
    judge_name: str
    judge_key: str

    log_file: str | None = None
    log_level: int = logging.INFO

    only_executors: list[str] | None = None
    exclude_executors: list[str] | None = None

    # TODO: Add command argument for populating this
    problem_storage_globs: list[str] | None = None

    # Flags
    ansi: bool = True
    do_self_tests: bool = True
    ssl_enabled: bool = False
    watchdog: bool = True

    graders: GraderManagerConfig = field(default_factory=GraderManagerConfig)
    executors: ExecutorManagerConfig = field(
        default_factory=ExecutorManagerConfig
    )
