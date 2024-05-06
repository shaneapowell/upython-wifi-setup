
import os


def file_exists(filename) -> bool:
    try:
        os.stat(filename)
        return True
    except OSError:
        return False
