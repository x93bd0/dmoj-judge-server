from .utils.builtin_int_patch import install as install_int_patch
from .problems import ProblemsManager
from .pm import PacketManager
from .config import Config
from .judge import Judge

from typing import Any
import argparse
import logging
import yaml
import os


def load_argument(
    args: argparse.Namespace, config_defaults: dict[str, Any], argname: str
) -> Any:
    arg: Any | None = getattr(
        args, argname, getattr(config_defaults, argname, None)
    )
    if not arg:
        # TODO: Better exceptions
        raise AttributeError(argname)
    return arg


def load_configuration(args: argparse.Namespace) -> Config:
    config_dict: dict[str, Any] = {}
    if args.config_file:
        with open(os.path.expanduser(args.config_file)) as fd:
            # TODO: Better exceptions
            config_data = yaml.load(fd, yaml.Loader)
            if isinstance(config_data, dict):
                config_dict.update(config_data)

    server_host: str = load_argument(args, config_dict, "server_host")
    config = Config(
        load_argument(args, config_dict, "server_host"),
        load_argument(args, config_dict, "server_port"),
        load_argument(args, config_dict, "judge_name"),
        load_argument(args, config_dict, "judge_key"),
    )

    for key, value in config_dict.items():
        getattr(config, key)  # Used for avoiding non-present fields
        setattr(config, key, value)

    if args.log_file:
        config.log_file = args.log_file

    if args.log_level:
        config.log_level = args.log_level

    if args.only_executors:
        config.only_executors = args.only_executors

    if args.no_ansi:
        config.ansi = False

    if args.skip_self_tests:
        config.do_self_tests = False

    if args.no_watchdog:
        config.watchdog = False

    return config


def main() -> None:
    # TODO: sanity_check

    parser = argparse.ArgumentParser(
        description="Spawns a judge for a submission server."
    )

    parser.add_argument(
        "server_host", nargs="?", help="host to connect for the server"
    )
    parser.add_argument(
        "judge_name", nargs="?", help="judge name (overrides configuration)"
    )
    parser.add_argument(
        "judge_key", nargs="?", help="judge key (overrides configuration)"
    )
    parser.add_argument(
        "-p",
        "--server-port",
        type=int,
        default=9999,
        help="port to connect for the server",
    )

    parser.add_argument(
        "-c",
        "--config-file",
        type=str,
        default="~/.dmojrc",
        help="file to load judge configurations from (default: ~/.dmojrc)",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_const",
        const=logging.DEBUG,
        default=logging.INFO,
        dest="log_level",
    )

    parser.add_argument("-l", "--log-file", help="log file to use")
    parser.add_argument(
        "--no-watchdog",
        action="store_true",
        help="disable use of watchdog on problem directories",
    )
    parser.add_argument(
        "-a",
        "--api-port",
        type=int,
        default=None,
        help="port to listen for the judge API (do not expose to public, "
        "security is left as an exercise for the reverse proxy)",
    )
    parser.add_argument(
        "-A",
        "--api-host",
        default="127.0.0.1",
        help="IPv4 address to listen for judge API",
    )
    parser.add_argument(
        "-s", "--secure", action="store_true", help="connect to server via TLS"
    )
    parser.add_argument(
        "-k",
        "--no-certificate-check",
        action="store_true",
        help="do not check TLS certificate",
    )
    parser.add_argument(
        "-T",
        "--trusted-certificates",
        default=None,
        help="use trusted certificate file instead of system",
    )

    executors = parser.add_mutually_exclusive_group()
    executors.add_argument(
        "-e",
        "--only-executors",
        help="only listed executors will be loaded (comma-separated)",
    )
    executors.add_argument(
        "-x",
        "--exclude-executors",
        help="prevent listed executors from loading (comma-separated)",
    )

    parser.add_argument(
        "--no-ansi", action="store_true", help="disable ANSI output"
    )
    parser.add_argument(
        "--skip-self-tests",
        action="store_true",
        help="skip executor self-tests",
    )
    parser.add_argument(
        "--no-install-int-patch",
        action="store_true",
        help="don't patch Python int object (Not recommended!)",
    )

    args = parser.parse_args()
    if not args.no_install_int_patch:
        install_int_patch()

    config: Config = load_configuration(args)
    del parser, args

    # TODO: unicode_stdout_stderr
    logging.basicConfig(
        filename=config.log_file,
        level=config.log_level,
        format="%(levelname)s %(asctime)s %(process)d %(module)s %(message)s",
    )

    # TODO: setproctitle
    probm = ProblemsManager(config)

    pm = PacketManager(config)
    pm.connect(
        probm.problems, {"PY3": [("python3", (3, 13, 3))]}
    )  # TODO: For test purposes; change me!
    pm.start()

    judge = Judge(config, pm, probm)
    judge.start()

    judge._receiver_handle.join()
