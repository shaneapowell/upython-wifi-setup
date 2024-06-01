import sys

COLOR_END = '\033[0m'
COLOR_BLUE = '\033[94m'
COLOR_GREEN = '\033[92m'
COLOR_YELLOW = '\033[93m'
COLOR_RED = '\033[91m'
BG_RED = '\u001b[41m'


def debug(tag, msg):
    print(f"{COLOR_BLUE}DEBUG{COLOR_END}[{tag}] - {msg}")


def info(tag, msg):
    print(f"{COLOR_GREEN}INFO{COLOR_END}[{tag}] - {msg}")


def warn(tag, msg):
    print(f"{COLOR_YELLOW}WARN{COLOR_END}[{tag}] - {msg}")


def error(tag, msg, ex: Exception | None = None):
    print(f"{COLOR_RED}ERROR{COLOR_END}[{tag}] - {msg}")
    if ex is not None:
        sys.print_exception(ex)  # type:ignore [attr-defined]


def fatal(tag, msg):
    print(f"{BG_RED}FATAL{COLOR_END}[{tag}] - {msg}")
