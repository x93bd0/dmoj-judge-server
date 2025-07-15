from enum import Enum
from dataclasses import dataclass
import dmoj_judge


class ResultKind(Enum):
    IE = (1 << 30, "red")
    TLE = (1 << 2, "white")
    MLE = (1 << 3, "yellow")
    OLE = (1 << 6, "yellow")
    RTE = (1 << 1, "yellow")
    IR = (1 << 4, "yellow")
    WA = (1 << 0, "red")
    SC = (1 << 5, "magenta")
    AC = (0, "green")


@dataclass
class Result:
    case: "dmoj_judge.problem.TestCase"
    result_flag: int = 0
    execution_time: float = 0
    wall_clock_time: float = 0
    max_memory: int = 0
    context_switches: tuple[int, int] = (0, 0)
    runtime_version: str = ""
    proc_output: bytes = b""
    _feedback: str = ""
    extended_feedback: str = ""
    points: float = 0

    @property
    def main_code(self) -> int:
        for kind in ResultKind:
            code: int = kind.value[0]
            if self.result_flag & code:
                return code
        return ResultKind.AC.value[0]

    @property
    def readable_codes(self) -> list[str]:
        execution_verdict: list[str] = []
        for kind in ResultKind:
            if self.result_flag & kind.value[0]:
                execution_verdict.append(kind.name)
        return execution_verdict

    @property
    def total_points(self) -> float:
        return self.case.points

    @property
    def output(self) -> str:
        return self.proc_output[: self.case.output_prefix_length].decode(
            "utf-8", "replace"
        )

    @property
    def feedback(self) -> str:
        # FIXME: Uninmplemented; dummy.
        return self.feedback


class CheckerResult:
    pass
