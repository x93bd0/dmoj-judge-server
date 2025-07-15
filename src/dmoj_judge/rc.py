import os
from multiprocessing import cpu_count as _get_cpu_count


CPU_COUNT: int = _get_cpu_count()


if hasattr(os, "getloadavg"):

    def load_fair() -> tuple[str, float]:
        load: float
        try:
            load = os.getloadavg()[0] / CPU_COUNT
        except OSError:
            load = -1
        return "load", load

else:

    def load_fair() -> tuple[str, float]:
        load: float
        try:
            with open("/proc/loadvg", "r") as fd:
                load = float(fd.read().split()[0]) / CPU_COUNT
        except (FileNotFoundError, ValueError):
            load = -1
        return "load", load


def cpu_count() -> tuple[str, int]:
    return "cpu-count", CPU_COUNT
