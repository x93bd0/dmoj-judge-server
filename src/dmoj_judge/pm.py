from .types import Problems, Executors
from typing import Any, TypeAlias
from threading import Thread
from .config import Config
from queue import Queue
import logging
import socket
import struct
import errno
import zlib
import json

log = logging.getLogger(__name__)
Packet: TypeAlias = dict[str, Any]
SIZE_PACKET = struct.Struct("!I")


# TODO: SSL
class PacketManager:
    config: Config
    _send_queue: Queue
    _sender_handle: Thread | None
    _socket: socket.SocketType | None

    def __init__(self, config: Config):
        self.config = config
        # TODO: SSL
        if config.ssl_enabled:
            raise NotImplementedError("SSL hasn't been implemented yet!")
        else:
            log.info("TLS not enabled.")

        self._send_queue = Queue()
        self._sender_handle = None
        self._socket = None

    def connect(
        self,
        problems: Problems,
        executors: Executors,
    ) -> None:
        if self._socket is not None:
            raise ValueError("PacketManager is already connected or dead")
        log.info(
            "Opening connection to: [%s]:%s",
            self.config.server_host,
            self.config.server_port,
        )

        while True:
            try:
                self._socket = socket.create_connection(
                    (self.config.server_host, self.config.server_port),
                    timeout=5,
                )  # TODO: Switch to timeout configuration
            except OSError as e:
                if e.errno != errno.EINTR:
                    raise
            else:
                break

        self._socket.settimeout(300)  # TODO: Switch to timeout configuration
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        # TODO: TLS
        log.info(
            "Starting handshake with: [%s]:%s",
            self.config.server_host,
            self.config.server_port,
        )
        self._handshake(problems, executors)

    def lazy_send_packet(self, packet: Packet) -> None:
        self._send_queue.put(packet)

    def send_packet(self, packet: Packet) -> None:
        assert self._socket is not None
        raw_packet: bytes = json.dumps(packet).encode("utf-8")
        cmp_packet: bytes = zlib.compress(raw_packet)
        self._socket.send(SIZE_PACKET.pack(len(cmp_packet)))
        self._socket.send(cmp_packet)

    def recv_packet(self) -> Packet:
        assert self._socket is not None
        size_packet: int = SIZE_PACKET.unpack(
            self._socket.recv(SIZE_PACKET.size)
        )[0]
        cmp_packet: bytes = self._socket.recv(size_packet)
        raw_packet: bytes = zlib.decompress(cmp_packet)
        return json.loads(raw_packet)

    def start(self) -> None:
        self._sender_handle = Thread(target=self._sender_thread, daemon=True)
        self._sender_handle.start()

    def _sender_thread(self) -> None:
        while True:
            packet: Packet = self._send_queue.get()
            self.send_packet(packet)

    def _handshake(
        self,
        problems: Problems,
        executors: Executors,
    ) -> None:
        self.send_packet(
            {
                "name": "handshake",
                "problems": problems,
                "executors": executors,
                "id": self.config.judge_name,
                "key": self.config.judge_key,
            }
        )

        log.info(
            "Awaiting handshake response: [%s]:%s",
            self.config.server_host,
            self.config.server_port,
        )

        try:
            packet: Packet = self.recv_packet()
        except Exception:
            log.exception(
                "Cannot understand handshake response: [%s]:%s",
                self.config.server_host,
                self.config.server_port,
            )
            raise Exception(
                "Couldn't authenticate (TODO: Replace with a more specific exception)"
            )
        else:
            if packet["name"] != "handshake-success":
                log.error("Handshake failed.")
                raise Exception(
                    "Couldn't authenticate (TODO: Replace with a more specific exception)"
                )

        # TODO: Better log string
        log.info(
            "Done handshake without errors: [%s]:%s",
            self.config.server_host,
            self.config.server_port,
        )
