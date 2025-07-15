from .base import BaseGrader
from .standard import StandardGrader
from ..errors import InvalidGraderNameError
from ..config import GraderManagerConfig
import importlib.util
import logging
import os

log = logging.getLogger(__name__)


class GraderManager:
    graders: dict[str, type[BaseGrader]]
    config: GraderManagerConfig

    def __init__(self, config: GraderManagerConfig):
        self.config = config
        self.graders = {}

        if self.config.include_builtin:
            self._load_builtin()

        for grader_id, grader_path in self.config.external.items():
            self._load_external_grader_module(grader_id, grader_path)

    def __setitem__(self, key: str, grader: BaseGrader):
        assert issubclass(grader, BaseGrader)
        assert key not in self.graders
        log.debug(f"Loaded `{key}` grader")
        self.graders[key] = grader

    def __getitem__(self, key: str) -> BaseGrader:
        try:
            return self.graders[key]

        except KeyError:
            raise InvalidGraderNameError(key)

    def _load_builtin(self) -> None:
        log.debug("Loading builtin graders")
        self["standard"] = StandardGrader

    def _load_external_grader_module(self, identifier: str, path: str) -> None:
        path = os.path.realpath(path)
        log.debug("Loading external grader from `{path}`")
        spec = importlib.util.spec_from_file_location(
            f"external_grader.{identifier}", path
        )
        assert spec is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self[identifier] = module.Grader
