import os
from multiprocessing import cpu_count as _get_cpu_count

_cpu_count: int = _get_cpu_count()
if hasattr(os, "getloadavg"):

    def load_fair() -> tuple[str, float]:
        load: int
        try:
            load = os.getloadavg()[0] / _cpu_count
        except OSError:
            load = -1
        return "load", load

else:

    def load_fair() -> tuple[str, int]:
        try:
            with open("/proc/loadvg", "r") as fd:
                load = float(fd.read().split()[0]) / _cpu_count
        except (FileNotFoundError, ValueError):
            load = -1
        return "load", load


def cpu_count() -> tuple[str, int]:
    return "cpu-count", _cpu_count
