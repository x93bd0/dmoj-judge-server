from .pm import PacketManager, Packet
from .types import Submission
from .problems import ProblemsManager
from typing import Callable
from threading import Thread
from .config import Config
from .rc import load_fair, cpu_count
import logging
import time


log = logging.getLogger(__name__)


class Judge:
    pm: PacketManager
    probm:ProblemsManager

    config: Config
    report_callbacks: list[Callable[[], tuple[str, str]]]

    _receiver_handle: Thread | None

    def __init__(self, config: Config, pm: PacketManager, probm: ProblemsManager) -> None:
        self.pm = pm
        self.probm = probm

        self.config = config
        self.report_callbacks = [load_fair, cpu_count]

        self._receiver_handle = None

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
                    self.pm.send_packet(response)
                case "get-current-submission":
                    raise NotImplementedError("get-current-submission packet")
                case "submission-request":
                    self.pm.send_packet(
                        {
                            "name": "submission-acknowledged",
                            "submission-id": packet["submission-id"],
                        }
                    )

                    raise NotImplementedError("submission-request packet")
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

    def begin_grading(self, submission: Submission):
        raise NotImplementedError("begin-grading")

    def abort_grading(self):
        raise NotImplementedError("abort-grading")

    def shutdown(self):
        self.pm.close()
        self.abort_grading()
        # TODO: Find a way to remove this
        sys.exit(0)
