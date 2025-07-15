from .base import BaseExecutor
from ..errors import InvalidConfigurationError, InvalidExecutorNameError
from ..config import ExecutorManagerConfig
import importlib.util
import logging
import os

log = logging.getLogger(__name__)
BUILTIN_EXECUTORS: dict[str, type[BaseExecutor]] = {}


class ExecutorManager:
    graders: dict[str, type[BaseExecutor]]
    config: ExecutorManagerConfig

    def __init__(self, config: ExecutorManagerConfig):
        self.config = config
        self.graders = {}

        if self.config.include_builtin:
            self._load_builtin()

        for executor_id, executor_path in self.config.external.items():
            self._load_external_executor_module(executor_id, executor_path)

    def __setitem__(self, key: str, executor: BaseExecutor) -> None:
        assert issubclass(grader, BaseExecutor)
        assert key not in self.executors
        log.debug(f"Loaded `{key}` executor")
        self.executors[key] = grader

    def __getitem__(self, key: str) -> BaseExecutor:
        try:
            return self.graders[key]

        except KeyError:
            raise InvalidExecutorNameError(key)

    def _load_builtin(self) -> None:
        if self.config.builtin_whitelist and self.config.builtin_blacklist:
            raise InvalidConfigurationError(
                "`executors.builtin_whitelist` and `executors.builtin_blacklist` are mutually exclusive"
            )

        if self.config.builtin_whitelist:
            for exec_id in self.config.builtin_whitelist:
                if exec_id not in BUILTIN_EXECUTORS:
                    raise InvalidConfigurationError(
                        f"There is no builtin `Executor` named `{exec_id}`"
                    )
                self[exec_id] = BUILTIN_EXECUTORS[exec_id]
            return

        log.debug("Loading builtin executors")
        blacklisted: list[str] = self.config.builtin_blacklist or []
        for executor_id, executor in BUILTIN_EXECUTORS:
            if executor_id in blacklisted:
                continue
            self[exec_id] = executor
        log.debug("Loaded builtin executors")

    def _load_external_executor_module(
        self, identifier: str, path: str
    ) -> None:
        path = os.path.realpath(path)
        log.debug("Loading external executor from `{path}`")
        spec = importlib.util.spec_from_file_location(
            f"external_grader.{identifier}", path
        )
        assert spec is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self[identifier] = module.Executor
