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

CPTBOX_LANG: str = "c++"
CPTBOX_SRC: list[str] = [
    "_cptbox.cpp" if not HAS_PYX else "_cptbox.pyx",
    "helper.cpp",
    "ptbox/ptdebug.cpp",
    "ptbox/ptdebug_x86.cpp",
    "ptbox/ptdebug_x64.cpp",
    "ptbox/ptdebug_arm.cpp",
    "ptbox/ptdebug_arm64.cpp",
    "ptbox/ptdebug_freebsd_x64.cpp",
    "ptbox/ptproc.cpp",
]

CPTBOX_HEADERS: list[str] = [
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

CPTBOX_INCLUDEDIRS: list[str] = [
    os.path.realpath(os.path.join(SRC_DIR, "dmoj_judge", "cptbox"))
]

CPTBOX_SRC = [
    os.path.join(SRC_DIR, "dmoj_judge", "cptbox", src) for src in CPTBOX_SRC
]

CPTBOX_HEADERS = [
    os.path.join(SRC_DIR, "dmoj_judge", "cptbox", src) for src in CPTBOX_HEADERS
]

CPTBOX_LIBS: list[str] = ["rt"]
if sys.platform.startswith("freebsd"):
    CPTBOX_LIBS.append("procstat")
else:
    CPTBOX_LIBS.append("seccomp")

setup(
    ext_modules=cythonize(
        [
            Extension(
                "dmoj_judge.cptbox._cptbox",
                sources=(
                    CPTBOX_SRC
                    if not SDIST_MODE
                    else (CPTBOX_SRC + CPTBOX_HEADERS)
                ),
                language=CPTBOX_LANG,
                libraries=CPTBOX_LIBS,
                include_dirs=CPTBOX_INCLUDEDIRS,
            )
        ]
    ),
)
