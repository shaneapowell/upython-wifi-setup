import sys
# Allow sys.path override via command-line arg for emulator/device testing.
# Usage: micropython test_wifi.py src  (emulator, src path)
# Usage: micropython test_wifi.py dist (emulator, dist path)
# Usage: mpremote run test_wifi.py     (device, /lib already on path)
if len(sys.argv) > 1:
    sys.path.insert(0, sys.argv[1])

import os
import unittest

import uwifisetup.wifi as wifi


class TestCredentials(unittest.TestCase):

    def setUp(self):
        if util_file_exists(wifi.CREDS_FILE):
            os.remove(wifi.CREDS_FILE)

    def tearDown(self):
        if util_file_exists(wifi.CREDS_FILE):
            os.remove(wifi.CREDS_FILE)

    def test_no_credentials_initially(self):
        self.assertFalse(wifi.hasCredentials())

    def test_save_and_load_credentials(self):
        wifi.saveCredentials("test_ssid", "test_password")
        self.assertTrue(wifi.hasCredentials())
        creds = wifi.loadCredentials()
        self.assertEqual(creds, ("test_ssid", "test_password"))

    def test_load_credentials_after_reset(self):
        wifi.saveCredentials("test_ssid", "test_password")
        wifi.factoryReset()
        self.assertFalse(wifi.hasCredentials())

    def test_load_nonexistent_credentials(self):
        result = wifi.loadCredentials()
        self.assertIsNone(result)

    def test_factory_reset_without_credentials(self):
        wifi.factoryReset()
        self.assertFalse(wifi.hasCredentials())


def util_file_exists(filename):
    try:
        os.stat(filename)
        return True
    except OSError:
        return False


if __name__ == "__main__":
    unittest.main()
