from multiprocessing.connection import Connection
from multiprocessing import Process, Pipe
from .types import Submission
from enum import Enum, auto
from typing import Generator
import logging


log = logging.getLogger(__name__)


class IPCRequest(Enum):
    ABORT = auto()


class IPCResponse(Enum):
    UNHANDLED_EXCEPTION = auto()
    COMPILE_MESSAGE = auto()
    COMPILE_ERROR = auto()
    GRADING_BEGIN = auto()
    GRADING_ABORTED = auto()
    GRADING_END = auto()
    BATCH_BEGIN = auto()
    BATCH_END = auto()
    HELLO = auto()
    RESULT = auto()
    BYE = auto()


class JudgeWorker:
    submission: Submission
    process: Process | None
    _conn: Connection

    def __init__(self, submission: Submission) -> None:
        self.submission = submission
        self.process = None

    def start(self) -> None:
        assert self.process is None
        handler = WorkerHandler(self.submission)
        self._conn, child_conn = Pipe()
        self.process = Process(
            name="DMOJ Judge Handler for %s/%d"
            % (self.submission.problem_id, self.submission.id),
            target=handler.start,
            args=(child_conn,),
        )
        self.process.start()
        # TODO: child_conn.close()?

    def request_abort_grading(self) -> None:
        assert self._conn
        try:
            self._conn.send((IPCRequest.ABORT, ()))
        except EOFError:
            log.exception(
                "Failed to send abort request to worker, did it race?"
            )


class WorkerHandler:
    submission: Submission

    def __init__(self, submission: Submission):
        self.submission = submission

    def start(self, conn: Connection) -> None:
        # TODO: setproctitle
        raise NotImplementedError("handler-start")

    def grade_cases(self) -> Generator[tuple[IPCResponse, tuple], None, None]:
        raise NotImplementedError("grade-cases")
