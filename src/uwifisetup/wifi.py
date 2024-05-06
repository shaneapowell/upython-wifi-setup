import uasyncio as asyncio
import network
import os
import json
import uwifisetup.log as log
import uwifisetup.util as util


CREDS_FILE = "/creds.json"
_KEY_SSID = "ssid"
_KEY_PWD = "pwd"


def hasCredentials() -> bool:
    """
    return the credentials status. If the setup has run,
    we'll have valid credentails on hand.  return True
    If not, .. well.. we won't. return False
    """
    return util.file_exists(CREDS_FILE)


def factoryReset():
    """
    Purge/Delete the creds file. Which will
    result in a "setup" stage being started next time.
    """
    log.info(__name__, "Clearing wifi creds")
    if hasCredentials():
        os.remove(CREDS_FILE)


def saveCredentials(ssid: str, pwd: str):
    """
    Save the values to the creds file.
    line 0 = ssid
    line 1 = pwd
    """
    log.info(__name__, "Saving wifi creds")
    with open(CREDS_FILE, "w") as f:
        creds = {_KEY_SSID: ssid, _KEY_PWD: pwd}
        json.dump(creds, f)


def loadCredentials() -> tuple[str, str] | None:
    """
    Read the creds from the file.
    """
    log.info(__name__, "Loading wifi creds")

    try:
        with open(CREDS_FILE, "r") as f:
            creds = json.load(f)
            ssid = creds[_KEY_SSID] if _KEY_SSID in creds else None
            pwd = creds[_KEY_PWD] if _KEY_PWD in creds else None
            return (ssid, pwd)
    except Exception as e:
        log.error(__name__, f"Failure loading creds file [{e}].")
        return None


def getWifi():
    """
    Return the singleton wifi instance.
    Just a simple clean wrapper around
    `network.WLAN(network.STA_IF)`.
    Here just for added convence.
    """
    return network.WLAN(network.STA_IF)


async def connectWifi(deviceName) -> bool:
    """
    Attempt to Connect to the configure wifi, assuming a config has been
    setup. This will always return success if a wifi has been configure, because
    the attempts to connect will continue indefinitely.
    However, if no credentials are yet setup, this will return a False.
    The connection status of the wifi is obtainable from the _wifi
    instance via self.getWifi() function.  Which is the same as calling `network.WLAN(network.STA_IF)`
    """
    log.info(__name__, f"Connecting to wifi as [{deviceName}]")
    if not hasCredentials():
        log.warn(__name__, "No Credentials Found")
        return False

    creds = loadCredentials()

    if not creds:
        log.error(__name__, "Problem with loading creds. Connect to wifi failure.")
        return False

    network.hostname(deviceName)
    wifi = getWifi()

    if wifi.isconnected():
        wifi.disconnect()

    wifi.active(False)
    wifi.active(True)
    wifi.config(pm=wifi.PM_NONE)

    wifi.connect(creds[0], creds[1])

    # Wait up to 25 seconds to connect
    waitCount = 0
    while not wifi.isconnected():
        await asyncio.sleep(1)
        waitCount += 1

        if waitCount >= 25:
            log.info(__name__, f"Connection to [{creds[0]}] Timed Out")
            return False

    log.info(__name__, f"Connected to WiFi [{wifi.ifconfig()[0]}] @ [{creds[0]}]")

    return True
