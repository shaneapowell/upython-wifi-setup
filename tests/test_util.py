import sys
# Allow sys.path override via command-line arg for emulator/device testing.
# Usage: micropython test_util.py src  (emulator, src path)
# Usage: micropython test_util.py dist (emulator, dist path)
# Usage: mpremote run test_util.py     (device, /lib already on path)
if len(sys.argv) > 1:
    sys.path.insert(0, sys.argv[1])

import os
import unittest

import uwifisetup.util as util


class TestFileExists(unittest.TestCase):

    def test_existing_file(self):
        test_file = "/tmp/test_util_exists.txt"
        with open(test_file, "w") as f:
            f.write("test")
        self.assertTrue(util.file_exists(test_file))
        os.remove(test_file)

    def test_non_existing_file(self):
        self.assertFalse(util.file_exists("/tmp/nonexistent_file_xyz.txt"))


class TestFileDelete(unittest.TestCase):

    def test_delete_existing_file(self):
        test_file = "/tmp/test_util_delete.txt"
        with open(test_file, "w") as f:
            f.write("test")
        result = util.file_delete(test_file)
        self.assertTrue(result)
        self.assertFalse(util.file_exists(test_file))

    def test_delete_non_existing_file(self):
        result = util.file_delete("/tmp/nonexistent_file_xyz.txt")
        self.assertFalse(result)


class TestFileHash(unittest.TestCase):

    def test_md5_hash(self):
        test_file = "/tmp/test_util_hash.txt"
        with open(test_file, "w") as f:
            f.write("hello")
        hash_val = util.file_hash(test_file)
        self.assertEqual(hash_val, "5d41402abc4b2a76b9719d911017c592")
        os.remove(test_file)


class TestFileSize(unittest.TestCase):

    def test_file_size(self):
        test_file = "/tmp/test_util_size.txt"
        with open(test_file, "w") as f:
            f.write("hello")
        self.assertEqual(util.file_size(test_file), 5)
        os.remove(test_file)


if __name__ == "__main__":
    unittest.main()
