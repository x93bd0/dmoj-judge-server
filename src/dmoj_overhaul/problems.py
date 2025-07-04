from .config import Config
from .types import Problems
import logging
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
        self.reload_problems()

    def reload_problems(self) -> None:
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
                        f"Duplicate problem {problem} found at {problem_dir}, ignoring in favour of {self.problems_dirs[problem]}"
                    )
                    continue

                self.problems_dirs[problem] = problem_dir
                self.problems.append((problem, os.path.getmtime(problem_dir)))
