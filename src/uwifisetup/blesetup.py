from . import log
from . import ble
from . import wifi
from . import util
import uasyncio as asyncio  # type:ignore [import-untyped, import-not-found]
import network   # type:ignore [import-not-found]
import time
import machine  # type:ignore [import-not-found]
import ubinascii  # type:ignore [import-not-found]

FIELD_REQ = 'req'
FIELD_RESP = 'resp'
FIELD_RESP_CODE = 'resp_code'
FIELD_MSG = 'msg'
FIELD_DEVICE_NAME = 'device_name'
FIELD_SSID = "ssid"
FIELD_RSSI = "rssi"
FIELD_SECURE = "secure"
FIELD_PASSWORD = "password"
FIELD_IP_ADDR = "ip_addr"
FIELD_FILENAME = "filename"
FIELD_DATA = "data"
FIELD_TRUNCATE = "truncate"
FIELD_HASH = "hash"
FIELD_WRITTEN = "written"
FIELD_SIZE = "size"

REQ_GET_DEVICE_INFO = 'get_device_info'
REQ_GET_AVAILABLE_WIFI = 'get_available_wifi'
REQ_CONNECT_TO_WIFI = 'connect_to_wifi'
REQ_COMPLETE = 'complete'
REQ_WRITE_FILE = 'write_file'
REQ_FILE_HASH = 'file_hash'
REQ_DELETE_FILE = 'delete_file'

CODE_OK = 'ok'
CODE_DONE = 'done'
CODE_ERROR = 'error'

_wlan = network.WLAN(network.STA_IF)


async def _defaultCustomHandler(req: str, reqModel: dict) -> bool | None:
    """
    Default custom handler for BLE WiFi setup — does nothing. Override with your own.

    Built-in requests (get_device_info, connect_to_wifi, etc.) are handled first.
    Only unknown requests reach this handler.

    Use `ble.send(response_dict)` to send responses.
    Use `ble.stop()` to shut down the service.

    Return True (or None) if you handled the request.
    Return False if you did not (ble.py will log a warning).
    """
    return None


async def setupWifi(
        deviceName: str,
        deviceInfo: dict = {},
        advertiseAppearance: int = 0x002,
        resetDeviceWhenSetupComplete: bool = False,
        customHandler=_defaultCustomHandler):
    """
    Startup up a BLE Nordic UART instance to
    configure the wifi.

    `deviceName`: What  you'll see as the device name in the bluetooth scan.

    `advertiseAppearance`: Optionally change the advertise appearance icon

    `resetDeviceWhenSetupComplete`: Due to memory limitation, it is wise to reset this device after the setup is complete to free up resources.

    `customHandler`: Async function called for unknown requests not handled by
        the built-in WiFi setup protocol. Signature:
        async def myCustomHandler(reqModel: dict) -> bool | None
        Use `ble.send(response_dict)` to send responses.
        Return True (or None) if handled, False if not.
    """

    assert deviceName is not None, "deviceName is required"
    assert isinstance(deviceName, str), "deviceName must be a string"
    assert deviceInfo is not None, "deviceInfo is required"
    assert isinstance(deviceInfo, dict), "deviceInfo must be a dict"
    assert advertiseAppearance is not None, "advertiseAppearance is required"
    assert isinstance(advertiseAppearance, int), "advertiseAppearance must be an int"

    log.info(__name__, f"Starting BLE WiFi Setup [{deviceName}]")

    await ble.startUART(
        deviceName=deviceName,
        advertiseAppearance=advertiseAppearance,
        handler=lambda req: _processRequest(req, deviceName=deviceName, deviceInfo=deviceInfo, customHandler=customHandler))

    log.info(__name__, f"BLE WiFi Setup Complete... reset device [{resetDeviceWhenSetupComplete}]")
    if resetDeviceWhenSetupComplete:
        machine.reset()


def _makeResponse(req: str, values: dict | None = None, code: str = CODE_OK) -> dict:
    resp = {}
    resp[FIELD_RESP] = req
    resp[FIELD_RESP_CODE] = code

    if values is not None:
        resp = resp | values

    return resp


def _makeErrorResponse(req: str | None, msg: str) -> dict:
    resp = {}
    resp[FIELD_RESP] = req or "ERR"
    resp[FIELD_RESP_CODE] = CODE_ERROR
    resp[FIELD_MSG] = msg
    return resp


def _handleAvailableWifi():
    _wlan.active(True)
    time.sleep(0.2)
    if _wlan.isconnected():
        _wlan.disconnect()
        time.sleep(0.2)
    log.info(__name__, "Scanning for available wifi networks...")
    scanResult = [{FIELD_SSID: n[0].decode(), FIELD_RSSI: n[3], FIELD_SECURE: n[4]} for n in _wlan.scan() if n[5] is False and len(n[0]) > 0]
    scanResult.sort(key=lambda r: r[FIELD_RSSI], reverse=True)
    log.info(__name__, f"Wifi Scan Result: [{scanResult}]")
    uniqueNames = set()

    for res in scanResult:
        if res[FIELD_SSID] not in uniqueNames:
            uniqueNames.add(res[FIELD_SSID])
            ble.send(_makeResponse(req=REQ_GET_AVAILABLE_WIFI, values=res))

    ble.send(_makeResponse(req=REQ_GET_AVAILABLE_WIFI, code=CODE_DONE))


def _handleConnectWifi(reqModel: dict):
    missingField = None

    if FIELD_SSID not in reqModel:
        missingField = FIELD_SSID
    elif FIELD_PASSWORD not in reqModel:
        missingField = FIELD_PASSWORD

    if missingField is not None:
        ble.send(_makeErrorResponse(req=REQ_CONNECT_TO_WIFI, msg=f"Missing Json Field [{missingField}]"))
        return

    ssid = reqModel[FIELD_SSID]
    password = reqModel[FIELD_PASSWORD]

    if ssid is None or len(ssid) <= 0:
        ble.send(_makeErrorResponse(req=REQ_CONNECT_TO_WIFI, msg=f"[{FIELD_SSID}]] cannot be empty"))
        return

    try:
        _wlan.active(True)
        time.sleep(0.5)

        if _wlan.isconnected():
            _wlan.disconnect()

        time.sleep(0.5)
        _wlan.connect(ssid, password)

        result = None
        sleepTime = 0
        while True:
            time.sleep(0.5)
            result = _wlan.status()
            if result != network.STAT_CONNECTING:
                break
            sleepTime += 1
            if sleepTime >= 20:
                sleepTime = -1
                break

        if sleepTime == -1:
            ble.send(_makeErrorResponse(req=REQ_CONNECT_TO_WIFI, msg="Timed Out"))
        else:
            if result == network.STAT_GOT_IP:
                log.info(__name__, f"Connected to [{ssid}] @ {_wlan.ifconfig()}")
                wifi.saveCredentials(ssid, password)
                ble.send(_makeResponse(req=REQ_CONNECT_TO_WIFI, values={FIELD_IP_ADDR: _wlan.ifconfig()[0]}))
            elif result == network.STAT_WRONG_PASSWORD:
                ble.send(_makeErrorResponse(req=REQ_CONNECT_TO_WIFI, msg="Password Error"))
            elif result == network.STAT_NO_AP_FOUND:
                ble.send(_makeErrorResponse(req=REQ_CONNECT_TO_WIFI, msg="Wifi Not In Range"))
            else:
                ble.send(_makeErrorResponse(req=REQ_CONNECT_TO_WIFI, msg="General Error"))

    except Exception as e:
        log.error(__name__, f"Unexpected Exception connecting to wifi {e}", e)
        ble.send(_makeErrorResponse(req=REQ_CONNECT_TO_WIFI, msg=f"Unexpected Exception [{e}]"))


def _normalizeFilename(filename: str) -> str:
    if not filename.startswith('/'):
        filename = '/' + filename
    return filename


def _handleWriteFile(reqModel: dict):
    missingField = None

    if FIELD_FILENAME not in reqModel:
        missingField = FIELD_FILENAME
    elif FIELD_DATA not in reqModel:
        missingField = FIELD_DATA

    if missingField is not None:
        ble.send(_makeErrorResponse(req=REQ_WRITE_FILE, msg=f"Missing Json Field [{missingField}]"))
        return

    filename = _normalizeFilename(reqModel[FIELD_FILENAME])
    data = reqModel[FIELD_DATA]
    truncate = reqModel.get(FIELD_TRUNCATE, False)

    try:
        decoded = ubinascii.a2b_base64(data)
    except Exception as e:
        ble.send(_makeErrorResponse(req=REQ_WRITE_FILE, msg=f"Invalid base64 data: [{e}]"))
        return

    try:
        mode = "wb" if truncate else "ab"
        with open(filename, mode) as f:
            f.write(decoded)
        log.info(__name__, f"write_file [{filename}] {'truncate' if truncate else 'append'} {len(decoded)} bytes")
        ble.send(_makeResponse(req=REQ_WRITE_FILE, values={FIELD_WRITTEN: len(decoded), FIELD_SIZE: util.file_size(filename)}))
    except Exception as e:
        ble.send(_makeErrorResponse(req=REQ_WRITE_FILE, msg=f"Failed to write file: [{e}]"))


def _handleFileHash(reqModel: dict):
    if FIELD_FILENAME not in reqModel:
        ble.send(_makeErrorResponse(req=REQ_FILE_HASH, msg=f"Missing Json Field [{FIELD_FILENAME}]"))
        return

    filename = _normalizeFilename(reqModel[FIELD_FILENAME])

    if not util.file_exists(filename):
        ble.send(_makeErrorResponse(req=REQ_FILE_HASH, msg=f"File not found: [{filename}]"))
        return

    try:
        h = util.file_hash(filename)
        ble.send(_makeResponse(req=REQ_FILE_HASH, values={FIELD_HASH: h}))
    except Exception as e:
        ble.send(_makeErrorResponse(req=REQ_FILE_HASH, msg=f"Failed to hash file: [{e}]"))


def _handleDeleteFile(reqModel: dict):
    if FIELD_FILENAME not in reqModel:
        ble.send(_makeErrorResponse(req=REQ_DELETE_FILE, msg=f"Missing Json Field [{FIELD_FILENAME}]"))
        return

    filename = _normalizeFilename(reqModel[FIELD_FILENAME])

    try:
        if util.file_delete(filename):
            log.info(__name__, f"delete_file [{filename}]")
            ble.send(_makeResponse(req=REQ_DELETE_FILE))
        else:
            ble.send(_makeErrorResponse(req=REQ_DELETE_FILE, msg=f"File not found: [{filename}]"))
    except Exception as e:
        ble.send(_makeErrorResponse(req=REQ_DELETE_FILE, msg=f"Failed to delete file: [{e}]"))


async def _processRequest(reqModel: dict, deviceName: str, deviceInfo: dict = {}, customHandler=_defaultCustomHandler):
    """
    Process a BLE WiFi Setup request and send response(s) via ble.send().
    Calls ble.stop() when a `complete` request is processed.
    Unknown requests are passed to customHandler.
    """
    if reqModel is None:
        ble.send(_makeErrorResponse(req=None, msg="Received Empty Request"))
        return

    if FIELD_REQ not in reqModel:
        ble.send(_makeErrorResponse(req=None, msg=f"Missing [{FIELD_REQ}]"))
        return

    req = reqModel[FIELD_REQ]

    if req == REQ_GET_DEVICE_INFO:
        ble.send(
            _makeResponse(
                req=req,
                values={FIELD_DEVICE_NAME: deviceName} | deviceInfo
            )
        )
        return

    if req == REQ_CONNECT_TO_WIFI:
        _handleConnectWifi(reqModel=reqModel)
        return

    if req == REQ_GET_AVAILABLE_WIFI:
        _handleAvailableWifi()
        return

    if req == REQ_COMPLETE:
        ble.send(_makeResponse(req=req))
        asyncio.sleep_ms(200)
        ble.stop()
        return

    if req == REQ_WRITE_FILE:
        _handleWriteFile(reqModel=reqModel)
        return

    if req == REQ_FILE_HASH:
        _handleFileHash(reqModel=reqModel)
        return

    if req == REQ_DELETE_FILE:
        _handleDeleteFile(reqModel=reqModel)
        return

    if customHandler is not _defaultCustomHandler:
        await customHandler(req, reqModel)
    else:
        ble.send(_makeErrorResponse(req=req, msg="Unknown Request"))
