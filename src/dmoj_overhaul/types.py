from typing import NamedTuple, TypeAlias, Any


Submission = NamedTuple(
    "Submission",
    [
        ("id", int),
        ("problem_id", str),
        ("language", str),
        ("source", str),
        ("time_limit", float),
        ("memory_limit", int),
        ("short_circuit", bool),
        ("meta", dict[str, Any]),
    ],
)

Problems: TypeAlias = list[tuple[str, float]]
Executors: TypeAlias = dict[str, list[tuple[str, tuple[int, ...]]]]
