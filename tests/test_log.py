import sys
# Allow sys.path override via command-line arg for emulator/device testing.
# Usage: micropython test_log.py src  (emulator, src path)
# Usage: micropython test_log.py dist (emulator, dist path)
# Usage: mpremote run test_log.py     (device, /lib already on path)
if len(sys.argv) > 1:
    sys.path.insert(0, sys.argv[1])

import unittest

import uwifisetup.log as log


class TestLogFunctions(unittest.TestCase):

    def test_debug_exists(self):
        self.assertTrue(callable(log.debug))

    def test_info_exists(self):
        self.assertTrue(callable(log.info))

    def test_warn_exists(self):
        self.assertTrue(callable(log.warn))

    def test_error_exists(self):
        self.assertTrue(callable(log.error))

    def test_fatal_exists(self):
        self.assertTrue(callable(log.fatal))

    def test_debug_output(self):
        log.debug("test_tag", "test message")

    def test_info_output(self):
        log.info("test_tag", "test message")

    def test_warn_output(self):
        log.warn("test_tag", "test message")

    def test_error_output(self):
        log.error("test_tag", "test message")

    def test_fatal_output(self):
        log.fatal("test_tag", "test message")

    def test_error_with_exception(self):
        try:
            raise ValueError("test error")
        except ValueError as e:
            log.error("test_tag", "error occurred", ex=e)


if __name__ == "__main__":
    unittest.main()
