from typing import Any


class InternalError(Exception):
    pass


class OutputLimitExceeded(Exception):
    # TODO: Type stream
    def __init__(self, stream: Any, limit: int):
        super().__init__(
            "exceeded %d-byte limit on %s stream" % (limit, stream)
        )
