from dataclasses import dataclass
from ..cptbox.filesystem_policies import (
    FilesystemAccessRule,
    RecursiveDir,
    ExactFile,
    ExactDir,
)
from typing import Any
import sys
import os


@dataclass
class Filesystem:
    read: list[FilesystemAccessRule]
    write: list[FilesystemAccessRule]

    @staticmethod
    def default() -> "Filesystem":
        usr_dir: list[FilesystemAccessRule]
        if os.path.isdir("/usr/home"):
            usr_dir = [
                RecursiveDir(f"/usr/{d}")
                for d in os.listdir("/usr")
                if d != "home" and os.path.isdir(f"/usr/{d}")
            ]
        else:
            usr_dir = [RecursiveDir("/usr")]

        base_fs: list[FilesystemAccessRule] = [
            ExactFile("/dev/null"),
            ExactFile("/dev/tty"),
            ExactFile("/dev/zero"),
            ExactFile("/dev/urandom"),
            ExactFile("/dev/random"),
            *usr_dir,
            RecursiveDir("/lib"),
            RecursiveDir("/lib32"),
            RecursiveDir("/lib64"),
            RecursiveDir("/opt"),
            ExactDir("/etc"),
            ExactFile("/etc/localtime"),
            ExactFile("/etc/timezone"),
            ExactDir("/usr"),
            ExactDir("/tmp"),
            ExactDir("/"),
        ]

        if "freebsd" in sys.platform:
            base_fs += [
                ExactFile("/etc/spwd.db"),
                ExactFile("/etc/pwd.db"),
                ExactFile("/dev/hv_tsc"),
                RecursiveDir("/dev/fd"),
            ]
        else:
            base_fs += [
                ExactDir("/sys/devices/system/cpu"),
                ExactFile("/sys/devices/system/cpu/online"),
                ExactFile("/etc/selinux/config"),
                ExactFile("/sys/kernel/mm/transparent_hugepage/enabled"),
                ExactFile("/sys/kernel/mm/transparent_hugepage/hpage_pmd_size"),
                ExactFile("/sys/kernel/mm/transparent_hugepage/shmem_enabled"),
            ]

        if sys.platform.startswith("freebsd"):
            base_fs += [
                ExactFile("/etc/libmap.conf"),
                ExactFile("/var/run/ld-elf.so.hints"),
            ]
        else:
            base_fs += [
                ExactDir("/proc"),
                ExactDir("/proc/self"),
                ExactFile("/proc/self/maps"),
                ExactFile("/proc/self/exe"),
                ExactFile("/proc/self/auxv"),
                ExactFile("/proc/meminfo"),
                ExactFile("/proc/stat"),
                ExactFile("/proc/cpuinfo"),
                ExactFile("/proc/filesystems"),
                ExactDir("/proc/xen"),
                ExactFile("/proc/uptime"),
                ExactFile("/proc/sys/vm/overcommit_memory"),
            ]

            base_fs += [
                ExactFile("/etc/ld.so.nohwcap"),
                ExactFile("/etc/ld.so.preload"),
                ExactFile("/etc/ld.so.cache"),
            ]

        write_fs: list[FilesystemAccessRule] = [ExactFile("/dev/null")]
        return Filesystem(base_fs, write_fs)

    @staticmethod
    def from_config(config: Any) -> "Filesystem":
        raise NotImplementedError("Filesystem.from_config")
