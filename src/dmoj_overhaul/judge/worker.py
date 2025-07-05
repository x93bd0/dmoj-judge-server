from multiprocessing.connection import Connection
from multiprocessing import Process, Pipe
from typing import Generator, Any
from ..types import Submission
from ..problem import Problem
from threading import Thread
from enum import Enum, auto
import traceback
import logging
import sys


log = logging.getLogger(__name__)


class IPCRequest(Enum):
    ABORT = auto()
    CLOSE = auto()


class IPCMessage(Enum):
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
    problem: Problem
    process: Process | None
    _conn: Connection | None

    def __init__(self, submission: Submission, problem: Problem) -> None:
        self.submission = submission
        self.problem = problem
        self.process = None
        self._conn = None

    def start(self) -> None:
        assert self.process is None
        handler = WorkerHandler(self.submission, self.problem)
        self._conn, child_conn = Pipe()
        self.process = Process(
            name="DMOJ Judge Handler for %s/%d"
            % (self.submission.problem_id, self.submission.id),
            target=handler.main,
            args=(child_conn,),
        )
        self.process.start()
        # TODO: child_conn.close()?

    def poll_messages(self) -> Generator[tuple[IPCMessage, tuple], None, None]:
        recv_timeout: int = max(60, int(2 * self.submission.time_limit))
        while True:
            msg_kind: IPCMessage
            msg_data: tuple

            try:
                if not self._conn.poll(timeout=recv_timeout):
                    raise TimeoutError(
                        "Worker did not send a message in %d seconds"
                        % recv_timeout
                    )
                msg_kind, msg_data = self._conn.recv()
            except TimeoutError:
                log.error(
                    "Worker has not sent a message in %d seconds, so it was killed"
                    % recv_timeout
                )
            except EOFError:
                # TODO: Implement custom TimeoutError raise
                raise
            except Exception:
                log.error("Failed to read IPC message from worker!")
                raise

            if msg_kind == IPCMessage.BYE:
                # TODO: Couldn't this fail?
                self._conn.send((IPCRequest.CLOSE, ()))
                return
            yield msg_kind, msg_data

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
    problem: Problem
    _aborted: bool

    def __init__(self, submission: Submission, problem: Problem):
        self.submission = submission
        self.problem = problem
        self._aborted = False

    @staticmethod
    def _report_unhandled_exception(conn: Connection) -> None:
        message = "".join(traceback.format_exception(*sys.exc_info()))
        conn.send((IPCMessage.UNHANDLED_EXCEPTION, (message,)))
        conn.send((IPCMessage.BYE, ()))

    def _receiver_thread(self, conn: Connection) -> None:
        while True:
            try:
                msg_kind, msg_data = conn.recv()
            except:
                log.exception("Judge unexpectedly hung up!")
                return self._do_abort()

            match msg_kind:
                case IPCRequest.ABORT:
                    self._do_abort()
                case IPCRequest.CLOSE:
                    return
                case _:
                    # FIXME: Wouldn't this hang the judge and disallow abort requests?
                    raise RuntimeError("")

    def _do_abort(self) -> None:
        self._aborted = True

    # TODO: Handle all errors correctly!
    def main(self, conn: Connection) -> None:
        # TODO: setproctitle

        _receiver_handle: Thread | None = None
        try:
            conn.send((IPCMessage.HELLO, ()))
            _receiver_handle = Thread(
                target=self._receiver_thread, args=(conn,)
            )
            _receiver_handle.start()

            case_gen = self.grade_cases()
            try:
                for msg in case_gen:
                    conn.send(msg)
            except BrokenPipeError:
                return self._report_unhandled_exception(conn)

            conn.send((IPCMessage.BYE, ()))
        except BrokenPipeError:  # TODO: Create tests that simulate this
            raise
        except:
            self._report_unhandled_exception(conn)
        finally:
            # TODO: Cleanup
            # TODO: Wait for _receiver_thread to exit
            pass

    def grade_cases(self) -> Generator[tuple[IPCMessage, tuple], None, None]:
        # TODO: Get grader
        yield IPCMessage.GRADING_BEGIN, (False,)
        # yield IPCMessage.GRADING_BEGIN, (self.problem.pretests_only)

        yield IPCMessage.GRADING_END, ()
