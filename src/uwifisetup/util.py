
import os


def file_exists(filename) -> bool:
    '''
    Nothing more than a simple re-useable doesTheFileExist function.
    '''
    try:
        os.stat(filename)
        return True
    except OSError:
        return False
