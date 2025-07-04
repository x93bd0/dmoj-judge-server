from ..pm import PacketManager, Packet
from ..types import Submission
from ..problems import ProblemsManager
from typing import Callable, Any
from threading import Thread, Lock, Event
from ..config import Config
from ..rc import load_fair, cpu_count
from .worker import JudgeWorker, IPCMessage
import logging
import time


log = logging.getLogger(__name__)


class Judge:
    pm: PacketManager
    probm: ProblemsManager

    config: Config
    report_callbacks: list[Callable[[], tuple[str, Any]]]

    worker: JudgeWorker | None

    _grading_lock: Lock
    _grading_handle: Thread | None
    _receiver_handle: Thread | None

    def __init__(
        self, config: Config, pm: PacketManager, probm: ProblemsManager
    ) -> None:
        self.pm = pm
        self.probm = probm

        self.config = config
        self.report_callbacks = [load_fair, cpu_count]

        self.worker = None

        self._grading_handle = None
        self._receiver_handle = None
        self._grading_lock = Lock()

    def start(self) -> None:
        self._receiver_handle = Thread(target=self._receiver_thread)
        self._receiver_handle.start()

    def _receiver_thread(self) -> None:
        while True:
            packet: Packet = self.pm.recv_packet()
            match packet.get("name", None):
                case "ping":
                    response: Packet = {
                        "name": "ping-response",
                        "when": packet["when"],
                        "time": time.time(),
                    }

                    for callback in self.report_callbacks:
                        key, value = callback()
                        response[key] = value
                    self.pm.lazy_send_packet(response)
                case "get-current-submission":
                    raise NotImplementedError("get-current-submission packet")
                case "submission-request":
                    self.pm.lazy_send_packet(
                        {
                            "name": "submission-acknowledged",
                            "submission-id": packet["submission-id"],
                        }
                    )

                    submission = Submission(
                        id=packet["submission-id"],
                        problem_id=packet["problem-id"],
                        language=packet["language"],
                        source=packet["source"],
                        time_limit=float(packet["time-limit"]),
                        memory_limit=int(packet["memory-limit"]),
                        short_circuit=packet["short-circuit"],
                        meta=packet["meta"],
                    )

                    self.begin_grading(submission)

                    log.info(
                        "Accepted submission: %d, executor: %s, code: %s",
                        submission.id,
                        submission.language,
                        submission.problem_id,
                    )
                case "terminate-submission":
                    raise NotImplementedError("terminate-submission packet")
                case "disconnect":
                    log.info("Received disconnect request, shutting down...")
                    return self.shutdown()
                case _:
                    log.error(
                        "Unknown packet %s, payload %s",
                        packet.get("name", None),
                        packet,
                    )

    def _grading_thread(self, ipc_ready_signal: Event) -> None:
        assert self.worker is not None
        submission_id: int = self.worker.submission.id
        batch: int = 0

        try:
            # TODO: Better logging
            for msg_kind, msg_data in self.worker.poll_messages():
                match msg_kind:
                    case IPCMessage.HELLO:
                        ipc_ready_signal.set()
                    case IPCMessage.COMPILE_ERROR:
                        log.info(
                            "Failed compiling submission!\n%s",
                            msg_data[0].rstrip(),
                        )

                        self.pm.lazy_send_packet(
                            {
                                "name": "compile-error",
                                "submission-id": submission_id,
                                "log": msg_data[0],
                            }
                        )
                    case IPCMessage.COMPILE_MESSAGE:
                        self.pm.lazy_send_packet(
                            {
                                "name": "compile-message",
                                "submission-id": submission_id,
                                "log": msg_data[0],
                            }
                        )
                    case IPCMessage.GRADING_BEGIN:
                        self.pm.lazy_send_packet(
                            {
                                "name": "grading-begin",
                                "submission-id": submission_id,
                                "pretested": msg_data[0],
                            }
                        )
                    case IPCMessage.GRADING_END:
                        self.pm.lazy_send_packet(
                            {
                                "name": "grading-end",
                                "submission-id": submission_id,
                            }
                        )
                    case IPCMessage.BATCH_BEGIN:
                        batch += 1
                        self.pm.lazy_send_packet(
                            {
                                "name": "batch-begin",
                                "submission-id": submission_id,
                            }
                        )
                    case IPCMessage.BATCH_END:
                        self.pm.lazy_send_packet(
                            {
                                "name": "batch-end",
                                "submission-id": submission_id,
                            }
                        )
                    case IPCMessage.GRADING_ABORTED:
                        self.pm.lazy_send_packet(
                            {
                                "name": "submission-terminated",
                                "submission-id": submission_id,
                            }
                        )
                    case IPCMessage.UNHANDLED_EXCEPTION:
                        # FIXME: Strip ANSI!
                        # Wait, is this really necessary?
                        self.pm.lazy_send_packet(
                            {
                                "name": "internal-error",
                                "submission-id": submission_id,
                                "message": msg_data[0],
                            }
                        )

                        log.warning(
                            "[CATCHED_EXCEPTION] No log handler on _grading_thread.IPC! (Error: %s)"
                            % msg_data[0]
                        )
                    case IPCMessage.RESULT:
                        self._handle_result(msg_data[0])

            log.info(
                "Done grading [%s]/[%s]",
                self.worker.submission.problem_id,
                self.worker.submission.id,
            )
        except Exception as e:
            # TODO: Log internal error
            log.warning(
                "[CATCHED_EXCEPTION] No log handler on _grading_thread! (Exception[%s]: %s)"
                % (type(e).__name__, str(e))
            )
        finally:
            # TODO: wait_with_timeout
            self.worker = None
            ipc_ready_signal.set()
            self._grading_lock.release()

    def _handle_result(self) -> None:
        raise NotImplementedError("_handle_result")

    def begin_grading(self, submission: Submission):
        self._grading_lock.acquire()
        assert self.worker is None

        log.info(
            "Started grading [%s]:%d in %s...",
            submission.problem_id,
            submission.id,
            submission.language,
        )

        self.worker = JudgeWorker(submission)
        self.worker.start()

        ipc_ready_signal = Event()
        self._grading_handle = Thread(
            target=self._grading_thread, args=(ipc_ready_signal,), daemon=True
        )

        self._grading_handle.start()
        ipc_ready_signal.wait()

    def abort_grading(self):
        raise NotImplementedError("abort-grading")

    def shutdown(self):
        self.pm.close()
        self.abort_grading()
        # TODO: Find a way to remove this
        sys.exit(0)
