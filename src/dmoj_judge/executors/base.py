from ..config import ExecutorConfig
from ..cptbox import IsolateTracer, TracedPopen, syscalls
from ..cptbox.filesystem_policies import FilesystemAccessRule, RecursiveDir
from ..cptbox.handlers import ALLOW
from ..errors import InternalError
from ..types import Result
from .filesystem import Filesystem
from typing import Any, Callable
from abc import ABCMeta, abstractmethod, abstractproperty
from subprocess import PIPE
import shutil
import os


SETBUFSIZE_PATH: str = None


# TODO: Is this really necessary?
# FIXME: Rewrite with correct typing
class ExecutorMeta(type):
    def __new__(mcs, name, bases, attrs) -> Any:
        if "__module__" in attrs:
            attrs["name"] = attrs["__module__"].split(".")[-1]
        return super().__new__(mcs, name, bases, attrs)


# TODO: Document
# TODO: Properties vs Get_*
class BaseExecutor(ABCMeta, metaclass=ExecutorMeta):
    # Used for caching purposes
    problem_id: str
    source_code: bytes
    unbuffered: bool

    # TODO: What's this?
    ext: str
    # TODO: What's this?
    nproc: int = 0
    # TODO: What's this?
    address_grace: int = 65536
    # TODO: What's this?
    data_grace: int = 0
    # TODO: Refactor to a more verbose name
    fsize: int = 0
    # TODO: What's this?
    personality: int = 0x0040000  # ADDR_NO_RANDOMIZE

    # TODO: What's the point of this if self.get_command() exists?
    command: str | None = None
    command_paths: list[str] = []
    # TODO: Pass Config down here (or a child of it [so it doesn't have to
    #         copy all of the configurations per worker])
    # TODO: Fix typing
    runtime_dict: dict[str, Any] = {}

    name: str
    test_program: str
    test_name: str = "self_test"

    config: ExecutorConfig
    filesystem: Filesystem
    allowed_syscalls: list[str | tuple[str, Any]]

    # TODO: What's this?
    _hints: list[str]
    _temp_dir: str
    working_dir: str | None = None

    def __init__(
        self,
        config: ExecutorConfig,
        problem_id: str,
        source_code: bytes,
        unbuffered: bool = False,
        dest_dir: str | None = None,
        hints: list[str] | None = None,
    ):
        self.config = config
        self.problem_id = problem_id
        self.source_code = source_code
        self.unbuffered = unbuffered

        self._temp_dir = dest_dir or config.temp_directory
        self._hints = hints or []
        self.working_dir = None

    def cleanup(self) -> None:
        raise NotImplementedError("Executor.cleanup")

    def __del__(self) -> None:
        self.cleanup()

    def get_executable(self) -> str | None:
        return None

    def get_nproc(self) -> int:
        return self.nproc

    def populate_result(
        self, stderr: bytes, result: Result, process: TracedPopen
    ) -> None:
        raise NotImplementedError("Executor.populate_result")

    # TODO: Find a better name
    def parse_feedback_from_stderr(
        self, stderr: bytes, process: TracedPopen
    ) -> str:
        return ""

    def get_security(
        self, extend_filesystem: Filesystem | None
    ) -> IsolateTracer:
        sec = IsolateTracer(
            read_fs=self.get_filesystem_access_rules(readable=True)
            + (extend_filesystem.read if extend_filesystem else []),
            write_fs=self.get_filesystem_access_rules(writeable=True)
            + (extend_filesystem.read if extend_filesystem else []),
        )

        for item in self.get_allowed_syscalls():
            if isinstance(item, tuple):
                name, handler = item
            else:
                name = item
                handler = ALLOW
            sec[getattr(syscalls, "sys_" + name)] = handler
        return sec

    def get_filesystem_access_rules(
        self, readable: bool = False, writeable: bool = False
    ) -> list[FilesystemAccessRule]:
        assert self.working_dir
        access_rules: list[FilesystemAccessRule] = [
            RecursiveDir(self.working_dir)
        ]
        if readable:
            access_rules.extend(self.filesystem.read)
        if writeable:
            access_rules.extend(self.filesystem.write)
        return access_rules

    def get_allowed_syscalls(self) -> list[str | tuple[str, Any]]:
        return self.allowed_syscalls

    def get_address_grace(self) -> int:
        return self.address_grace

    def get_env(self) -> dict[str, str]:
        env = {"LANG": "en_US.UTF8"}  # FIXME: Remove hardcoded language
        if self.unbuffered:
            env["CPTBOX_STDOUT_BUFFER_SIZE"] = "0"
        return env

    def launch(
        self,
        *args,
        time_limit: float = 0,
        memory_limit: int = 0,
        wall_time: float | None = None,
        stdin: int | None = PIPE,
        stdout: int | None = PIPE,
        stderr: int | None = None,
        stdout_buffer_size: int = 0,
        stderr_buffer_size: int = 0,
        extend_filesystem: Filesystem | None = None,
        symlinks: dict[str, str] | None = None,
    ) -> Any:
        assert self.working_dir is not None
        if symlinks:
            for src, dst in symlinks.items():
                src = os.path.abspath(os.path.join(self.working_dir, src))
                if (
                    os.path.commonprefix([src, self.working_dir])
                    != self.working_dir
                ):
                    raise InternalError(
                        "Cannot symlink outside of submission directory"
                    )

                if os.path.islink(src):
                    os.unlink(src)
                os.symlink(dst, src)

        # TODO: setbufsize.so
        agent: str = os.path.join(self.working_dir, "setbufsize.so")
        shutil.copyfile(SETBUFSIZE_PATH, agent)
        child_env: dict[str, str] = {
            "LD_LIBRARY_PATH": os.environ.get("LD_LIBRARY_PATH", ""),
            "LD_PRELOAD": agent,
            "CPTBOX_STDOUT_BUFFER_SIZE": str(stdout_buffer_size),
            "CPTBOX_STDERR_BUFFER_SIZE": str(stderr_buffer_size),
        }

        child_env.update(self.get_env())
        executable = self.get_executable()
        assert executable is not None

        return TracedPopen(
            # TODO: Which parameters does it need?
            [a.encode("utf-8") for a in self.get_cmdline() + list(args)],
            executable=executable.encode("utf-8"),
            security=self.get_security(extend_filesystem=extend_filesystem),
            time=time_limit,  # TODO: Why int?
            memory=memory_limit,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            env=child_env,
            nproc=self.get_nproc(),
            fsize=self.fsize,
            address_grace=self.get_address_grace(),
            data_grace=self.data_grace,
            personality=self.personality,
            cwd=self.working_dir.encode("utf-8"),
            wall_time=wall_time,
            cpu_affinity=self.config.submission_cpu_affinity,
        )

    @classmethod
    def get_name(cls) -> str:
        return cls.__module__.split(".")[-1]

    @classmethod
    def get_command(cls) -> str | None:
        return cls.runtime_dict.get(cls.command or "", None)

    # TODO: What's this?
    @classmethod
    def initialize(cls) -> bool:
        raise NotImplementedError("Executor.initialize")

    @classmethod
    def self_test(
        cls,
        output: bool = True,
        error_callback: Callable[[Any], Any] | None = None,
    ) -> bool:
        raise NotImplementedError("Executor.self_test")

    @classmethod
    def get_versionable_commands(cls) -> list[tuple[str, str]]:
        raise NotImplementedError("Executor.get_versionable_commands")

    @classmethod
    def get_runtime_versions(cls) -> Any:
        raise NotImplementedError("Executor.get_runtime_versions")

    @classmethod
    def parse_version(cls, command: str, output: str) -> Any:
        raise NotImplementedError("Executor.parse_version")

    @classmethod
    def get_version_flags(cls, command: str) -> Any:
        return ["--version"]

    @classmethod
    def find_command_from_list(cls, files: list[str]) -> str | None:
        raise NotImplementedError("Executor.find_command_from_list")

    @classmethod
    def autoconfig_find_first(cls, mapping: dict[str, list[str]] | None) -> Any:
        raise NotImplementedError("Executor.autoconfig_find_first")

    @classmethod
    def autoconfig_run_test(cls, result: Any) -> Any:
        raise NotImplementedError("Executor.autoconfig_run_test")

    # TODO: Find a better name
    @classmethod
    def get_find_first_mapping(cls) -> dict[str, list[str]] | None:
        raise NotImplementedError("Executor.get_find_first_mapping")

    @classmethod
    def autoconfig(cls) -> Any:
        raise NotImplementedError("Executor.autoconfig")

    @abstractmethod
    def create_files(self) -> None:
        pass

    @abstractmethod
    def get_cmdline(self, **kwargs) -> list[str]:
        pass
