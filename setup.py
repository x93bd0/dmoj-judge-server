from setuptools import setup, Extension
from Cython.Build import cythonize
import sys
import os

SRC_DIR: str = "src"
HAS_PYX: bool = os.path.exists(
    os.path.join(SRC_DIR, "dmoj_judge", "cptbox", "_cptbox.pyx")
)
# TODO: Find a way to replace this trick.
SDIST_MODE: bool = False
if len(sys.argv) > 1 and sys.argv[1] == "sdist":
    SDIST_MODE = True

CPTBOX_PKG: str = "dmoj_judge.cptbox._cptbox"
STD_CHECKER_PKG: str = "dmoj_judge.checkers._standard_checker"

EXTS: list[str] = [CPTBOX_PKG, STD_CHECKER_PKG]

EXT_LANG: dict[str, str] = {CPTBOX_PKG: "c++"}
EXT_PATH_PREFIX: dict[str, str] = {
    CPTBOX_PKG: os.path.join(SRC_DIR, "dmoj_judge", "cptbox"),
    STD_CHECKER_PKG: os.path.join(SRC_DIR, "dmoj_judge", "checkers"),
}

SRCS: dict[str, list[str]] = {
    CPTBOX_PKG: [
        "_cptbox.cpp" if not HAS_PYX else "_cptbox.pyx",
        "helper.cpp",
        "ptbox/ptdebug.cpp",
        "ptbox/ptdebug_x86.cpp",
        "ptbox/ptdebug_x64.cpp",
        "ptbox/ptdebug_arm.cpp",
        "ptbox/ptdebug_arm64.cpp",
        "ptbox/ptdebug_freebsd_x64.cpp",
        "ptbox/ptproc.cpp",
    ],
    STD_CHECKER_PKG: ["_standard_checker.c"],
}

HEADERS: dict[str, list[str]] = {
    CPTBOX_PKG: [
        "helper.h",
        "ptbox/ptbox.h",
        "ptbox/ptdebug_x86.h",
        "ptbox/ptdebug_x64.h",
        "ptbox/ptdebug_arm.h",
        "ptbox/ptdebug_arm64.h",
        "ptbox/ptdebug_freebsd_x64.h",
        "ptbox/ext_linux.h",
        "ptbox/ext_freebsd.h",
    ]
}

INCLUDEDIRS: dict[str, list[str]] = {
    CPTBOX_PKG: [
        os.path.realpath(os.path.join(SRC_DIR, "dmoj_judge", "cptbox"))
    ]
}

LIBS: dict[str, list[str]] = {CPTBOX_PKG: ["rt"]}

for ext_id in SRCS.keys():
    SRCS[ext_id] = [
        os.path.join(EXT_PATH_PREFIX[ext_id], src) for src in SRCS[ext_id]
    ]

for ext_id in HEADERS.keys():
    HEADERS[ext_id] = [
        os.path.join(EXT_PATH_PREFIX[ext_id], header)
        for header in HEADERS[ext_id]
    ]


if sys.platform.startswith("freebsd"):
    LIBS[CPTBOX_PKG].append("procstat")
else:
    LIBS[CPTBOX_PKG].append("seccomp")


extensions: list[Extension] = []
for ext_id in EXTS:
    sources: list[str] = SRCS[ext_id]
    if SDIST_MODE and ext_id in HEADERS:
        sources.extend(HEADERS[ext_id])

    language: str = EXT_LANG.get(ext_id, "c")
    libraries: list[str] = LIBS.get(ext_id, [])
    include_dirs: list[str] = INCLUDEDIRS.get(ext_id, [])
    extensions.append(
        Extension(
            ext_id,
            sources=sources,
            language=language,
            libraries=libraries,
            include_dirs=include_dirs,
        )
    )


setup(
    ext_modules=cythonize(extensions),
)
