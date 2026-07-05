
import os
import hashlib
import binascii


def file_exists(filename) -> bool:
    '''
    Nothing more than a simple re-useable doesTheFileExist function.
    '''
    try:
        os.stat(filename)
        return True
    except OSError:
        return False


def file_delete(filename) -> bool:
    '''
    A simple re-useable delete file function
    '''
    assert filename is not None, "filename requried"
    if file_exists(filename):
        os.remove(filename)
        return True
    return False


def file_hash(filename) -> str:
    '''
    Return the MD5 hex digest of a file's contents.
    '''
    with open(filename, "rb") as f:
        return binascii.hexlify(hashlib.md5(f.read()).digest()).decode('utf-8')


def file_size(filename) -> int:
    '''
    return the size of the file in bytes
    '''
    return os.stat(filename)[6]
