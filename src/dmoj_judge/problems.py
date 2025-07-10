from .problem import Problem, ProblemDataManager
from .config import Config, ProblemConfig
from .errors import InvalidInitException
from .types import Problems

from yaml.parser import ParserError
from yaml.scanner import ScannerError
from typing import Any
import zipfile
import logging
import yaml
import glob
import os


log = logging.getLogger(__name__)


class ProblemsManager:
    config: Config
    # TODO: Maybe add a cached approach instead? (or keep both, though
    #         realistically, it is almost impossible to reach an MLE with
    #         this method)
    problems: Problems
    problems_dirs: dict[str, str]

    def __init__(self, config: Config):
        self.config = config
        self.load_problems()

    def get_problem_root(self, id: str) -> str:
        return self.problems_dirs[id]

    def load_problems(self) -> None:
        assert self.config.problem_storage_globs
        self.problems = []
        self.problems_dirs = {}

        for dir_glob in self.config.problem_storage_globs:
            for problem_config in glob.iglob(
                os.path.join(dir_glob, "init.yml"), recursive=True
            ):
                if not os.access(problem_config, os.R_OK):
                    continue
                problem_dir: str = os.path.dirname(problem_config)
                problem = os.path.basename(problem_dir)

                if problem in self.problems_dirs:
                    log.warning(
                        "Duplicate problem %s found at %s, ignoring in favour of %s",
                        problem,
                        problem_dir,
                        self.problems_dirs[problem],
                    )
                    continue

                self.problems_dirs[problem] = problem_dir
                self.problems.append((problem, os.path.getmtime(problem_dir)))

    def load_problem(
        self,
        id: str,
        time_limit: float = 0,
        memory_limit: int = 0,
        meta: dict[str, Any] | None = None,
    ) -> Problem:
        if not meta:
            meta = {}

        dmanager = ProblemDataManager(self.get_problem_root(id))
        try:
            init: dict[str, Any] | Any = yaml.safe_load(dmanager["init.yml"])
            if not init:
                raise InvalidInitException(
                    "`init.yml` file of problem `%s` is empty" % (id,)
                )
            assert isinstance(init, dict)
        except (
            IOError,
            KeyError,
            ParserError,
            ScannerError,
            AssertionError,
        ) as e:
            raise InvalidInitException.from_exception(e)

        config = ProblemConfig(**init)
        if config.archive:
            archive_path: str = os.path.join(dmanager.root_path, config.archive)
            if not os.path.exists(archive_path):
                raise InvalidInitException(
                    "archive file `%s` doesn't exist" % (archive_path,)
                )

            try:
                dmanager.archive = zipfile.ZipFile(archive_path)
            except zipfile.BadZipFile as e:
                raise InvalidInitException.from_exception(e)

        return Problem(
            id=id,
            time_limit=time_limit,
            memory_limit=memory_limit,
            meta=meta,
            config=config,
            data_manager=dmanager,
        )
