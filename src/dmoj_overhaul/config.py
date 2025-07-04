from dataclasses import dataclass, field
from typing import Any
import logging


# TODO: Consider adding a root logger property for doing root_logger.getChild('pkg')
# TODO: Add API flags
@dataclass
class Config:
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


# FIXME: This wasn't tested nor investigated enough, so I can't ensure every
#         ProblemConfig can fit this schema the way the original DMOJ devs
#         intended.
@dataclass
class ProblemConfig:
    meta: dict[str, Any]

    wall_time_factor: int = 3
    output_prefix_length: int = 0
    output_limit_length: int = 25165824
    binary_data: bool = False
    short_circuit: bool = True
    dependencies: list = field(default_factory=list)
    points: int = 1
    symlinks: dict = field(default_factory=dict)
