from typing import Self
import builtins
import sys

INT_MAX_DIGITS = getattr(sys.int_info, "default_max_str_digits", 4300)
builtin_int = int


class patched_int_meta(type):
    def __instancecheck__(self, instance) -> bool:
        return isinstance(instance, builtin_int)

    def __subclasscheck__(cls, subclass) -> bool:
        return issubclass(subclass, builtin_int)

    def __eq__(self, other) -> bool:
        return self is other or other is builtin_int

    def __hash__(self) -> int:
        return hash(builtin_int)


class patched_int(builtin_int, metaclass=patched_int_meta):
    def __new__(cls: type[int], s=0, *args, **kwargs) -> Self:
        if isinstance(s, str) and len(s) > INT_MAX_DIGITS:
            raise ValueError("integer is too long")
        if cls is patched_int:
            cls = builtin_int
        return builtin_int.__new__(cls, s, *args, **kwargs)


def install() -> None:
    builtins.int, builtins.builtin_int = patched_int, builtin_int


def uninstall() -> None:
    builtins.int = builtin_int
