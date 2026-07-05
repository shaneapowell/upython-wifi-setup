from . import log
from uwifisetup import wifi
from uwifisetup import util
import uasyncio as asyncio  # type:ignore [import-untyped]
import ubluetooth as bluetooth  # type:ignore [import-not-found]
import aioble  # type:ignore [import-not-found]
import json
import network   # type:ignore [import-not-found]
import time
import machine  # type:ignore [import-not-found]
import ubinascii # type:ignore [import-not-found]
from micropython import const  # type:ignore [import-not-found]


FIELD_REQ = 'req'  # The RX json must include a req field
FIELD_RESP = 'resp'  # The TX json echos back the req field value
FIELD_RESP_CODE = 'resp_code'  # The TX json will include a status of 'ok' or 'error'
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

_GENERIC_ACCESS = bluetooth.UUID(0x1800)
_DEVICE_NAME = bluetooth.UUID(0x2A00)

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_RX = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
_GENERIC_COMPUTER = const(0x002)
_ADV_INTERVAL_US = const(250000)
_MAX_BUFFER_SIZE = const(1024)
_RX_TRIGGER_CHAR = '\r'

_wlan = network.WLAN(network.STA_IF)
_rx_buffer = ""



async def setupWifi(
        deviceName: str,
        deviceInfo: dict = {},
        advertiseAppearance: int = _GENERIC_COMPUTER,
        resetDeviceWhenSetupComplete: bool = False):
    """
    Startup up a BLE Nordic UART instance to
    configure the wifi.

    `deviceName`: What  you'll see as the device name in the bluetooth scan.

    `advertiseAppearance`: Optionally change the advertise appearance icon

    `resetDeviceWhenSetupComplete`: Due to memory limitation, it is wise to reset this device after the setup is complete to free up resources.

    """

    assert deviceName is not None, "deviceName is required"
    assert isinstance(deviceName, str), "deviceName must be a string"
    assert deviceInfo is not None, "deviceInfo is required"
    assert isinstance(deviceInfo, dict), "deviceInfo must be a dict"
    assert advertiseAppearance is not None, "advertiseAppearance is required"
    assert isinstance(advertiseAppearance, int), "advertiseAppearance must be an int"

    log.info(__name__, f"Starting BLE WiFi Setup [{deviceName}]")

    uartService = aioble.Service(_UART_UUID)
    # TX: Remote <- This
    txChar = aioble.Characteristic(uartService, _UART_TX, read=True, notify=True)
    # RX: Remote -> This
    rxChar = aioble.Characteristic(uartService, _UART_RX, write=True, capture=True)

    # Init the RX buffer to our apparent max of 256 bytes
    rxChar.write(bytearray(256))

    # Override the mpy default device-name characteristic. This seems to work, but if you
    # inspect the BLE device , it shows the 0x1800 primary service twice.
    # Seems that this doesn't overwrite the built-in service, but instead adds a 2nd one
    genericService = aioble.Service(_GENERIC_ACCESS)
    defaultName = aioble.Characteristic(genericService, _DEVICE_NAME, read=True, notify=True)
    defaultName.write(deviceName)

    aioble.register_services(genericService, uartService)

    isComplete = False

    while not isComplete:

        async with await aioble.advertise(interval_us=_ADV_INTERVAL_US,
                                          name=deviceName,
                                          services=[_UART_UUID, _GENERIC_ACCESS],
                                          appearance=advertiseAppearance) as connection:

            log.info(__name__, f"Connected from {connection.device}")

            _rx_buffer = ""

            while connection.is_connected():

                try:
                    con, data = await rxChar.written(timeout_ms=1000)
                    rawData = data.decode()
                    trigger = _RX_TRIGGER_CHAR in rawData

                    if trigger:
                        rawData = rawData.split(_RX_TRIGGER_CHAR, 1)[0]

                    _rx_buffer += rawData
                    _rx_buffer = _rx_buffer.strip()

                    if len(_rx_buffer) > _MAX_BUFFER_SIZE:
                        errorMessage = f"RX buffer overflow ({len(_rx_buffer)} bytes), flushing"
                        log.error(__name__, errorMessage)
                        if connection.is_connected():
                            _sendResponse(tx=txChar, rawResp=_generateErrorResponse(req=None, msg=errorMessage))
                        _rx_buffer = ""
                    elif len(_rx_buffer) == 0:
                        errorMessage = "Empty Request Received, ignored"
                        log.error(__name__, errorMessage)
                        if connection.is_connected():
                            _sendResponse(tx=txChar, rawResp=_generateErrorResponse(req=None, msg=errorMessage))
                        _rx_buffer = ""
                    elif trigger:
                        log.info(__name__, f"rx: {_rx_buffer}")

                        isComplete = await _processRequest(
                            rawReq=_rx_buffer,
                            tx=txChar,
                            deviceName=deviceName,
                            deviceInfo=deviceInfo)
                        if isComplete:
                            await connection.disconnect()
                        _rx_buffer = ""
                except asyncio.TimeoutError:
                    # We dont' really care. Just need a away to not hold us up if the connection closes
                    _rx_buffer = ""
                    pass
                except Exception as e:
                    _rx_buffer = ""
                    log.error(__name__, "Unexpected Error", ex=e)
                    if connection.is_connected():
                        _sendResponse(tx=txChar, rawResp=_generateErrorResponse(req=None, msg=f"Unexpected Error: {type(e).__name__}: {e}"))


                asyncio.sleep_ms(10)

    log.info(__name__, f"BLE WiFi Setup Complete... reset device [{resetDeviceWhenSetupComplete}]")
    if resetDeviceWhenSetupComplete:
        machine.reset()


def _sendResponse(tx: aioble.Characteristic, rawResp: str):
    """
    A simple send function to be shared
    """
    log.info(__name__, f"tx: {rawResp}")
    rawResp += '\r\n'
    tx.write(data=rawResp, send_update=True)


def _generateResponse(req: str, values: dict | None = None, code: str = CODE_OK) -> str:
    """
    Generate a success response.
    """
    resp = {}
    resp[FIELD_RESP] = req
    resp[FIELD_RESP_CODE] = code

    if values is not None:
        resp = resp | values

    return json.dumps(resp)


def _generateErrorResponse(req: str | None, msg: str) -> str:
    """
    Generate a standard error response json model
    """
    resp = {}
    resp[FIELD_RESP] = req or "ERR"
    resp[FIELD_RESP_CODE] = CODE_ERROR
    resp[FIELD_MSG] = msg
    return json.dumps(resp)


def _sendAvailableWifiResponse(tx: aioble.Characteristic):
    """
    Find all available wifi, and return the json responses one by one.
    """
    global _wlan
    _wlan.active(True)
    time.sleep(0.2)
    if _wlan.isconnected():
        _wlan.disconnect()
        time.sleep(0.2)
    log.info(__name__, "Scanning for available wifi networks...")
    scanResult = [{FIELD_SSID: n[0].decode(), FIELD_RSSI: n[3], FIELD_SECURE: n[4]} for n in _wlan.scan() if n[5] is False and len(n[0]) > 0]
    scanResult.sort(key=lambda r: r[FIELD_RSSI], reverse=True)  # Sort by RSSI
    log.info(__name__, f"Wifi Scan Result: [{scanResult}]")
    uniqueNames = set()

    for res in scanResult:
        if res[FIELD_SSID] not in uniqueNames:
            uniqueNames.add(res[FIELD_SSID])
            _sendResponse(tx=tx, rawResp=_generateResponse(req=REQ_GET_AVAILABLE_WIFI, values=res))

    _sendResponse(tx=tx, rawResp=_generateResponse(req=REQ_GET_AVAILABLE_WIFI, code=CODE_DONE))


def _attemptConnectWifi(tx: aioble.Characteristic, reqModel: dict):
    """
    Attempt to connect to the wifi identified in the reqModel
    """
    missingField = None

    if FIELD_SSID not in reqModel:
        missingField = FIELD_SSID
    elif FIELD_PASSWORD not in reqModel:
        missingField = FIELD_PASSWORD

    if missingField is not None:
        return _sendResponse(tx=tx, rawResp=_generateErrorResponse(req=REQ_CONNECT_TO_WIFI, msg=f"Missing Json Field [{missingField}]"))

    ssid = reqModel[FIELD_SSID]
    password = reqModel[FIELD_PASSWORD]

    if ssid is None or len(ssid) <= 0:
        return _sendResponse(tx=tx, rawResp=_generateErrorResponse(req=REQ_CONNECT_TO_WIFI, msg=f"[{FIELD_SSID}]] cannot be empty"))

    try:

        # Attempt connection ...
        _wlan.active(True)
        time.sleep(0.5)

        if _wlan.isconnected():
            _wlan.disconnect()

        time.sleep(0.5)
        _wlan.connect(ssid, password)

        # Wait for the connection. We'll timeout after 10 seconds.
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
            return _sendResponse(tx=tx, rawResp=_generateErrorResponse(req=REQ_CONNECT_TO_WIFI, msg="Timed Out"))
        else:
            if result == network.STAT_GOT_IP:
                log.info(__name__, f"Connected to [{ssid}] @ {_wlan.ifconfig()}")
                wifi.saveCredentials(ssid, password)
                return _sendResponse(tx=tx, rawResp=_generateResponse(req=REQ_CONNECT_TO_WIFI, values={FIELD_IP_ADDR: _wlan.ifconfig()[0]}))
            elif result == network.STAT_WRONG_PASSWORD:
                return _sendResponse(tx=tx, rawResp=_generateErrorResponse(req=REQ_CONNECT_TO_WIFI, msg="Password Error"))
            elif result == network.STAT_NO_AP_FOUND:
                return _sendResponse(tx=tx, rawResp=_generateErrorResponse(req=REQ_CONNECT_TO_WIFI, msg="Wifi Not In Range"))
            else:
                return _sendResponse(tx=tx, rawResp=_generateErrorResponse(req=REQ_CONNECT_TO_WIFI, msg="General Error"))

    except Exception as e:
        log.error(__name__, f"Unexpected Exception connecting to wifi {e}", e)
        return _sendResponse(tx=tx, rawResp=_generateErrorResponse(req=REQ_CONNECT_TO_WIFI, msg=f"Unexpected Exception [{e}]"))


def _normalizeFilename(filename: str) -> str:
    """
    Ensure filename is root-relative by prefixing '/' if missing.
    """
    if not filename.startswith('/'):
        filename = '/' + filename
    return filename


def _writeFile(tx: aioble.Characteristic, reqModel: dict):
    """
    Write a base64-encoded data chunk to a file.

    The `data` field in the request must be base64-encoded.
    It is decoded to raw bytes before being written to disk.

    If `truncate` is true, the file is opened in write mode (wb),
    overwriting any existing content. If false, the file is opened
    in append mode (ab), appending to existing content.
    """
    missingField = None

    if FIELD_FILENAME not in reqModel:
        missingField = FIELD_FILENAME
    elif FIELD_DATA not in reqModel:
        missingField = FIELD_DATA

    if missingField is not None:
        return _sendResponse(tx=tx, rawResp=_generateErrorResponse(req=REQ_WRITE_FILE, msg=f"Missing Json Field [{missingField}]"))

    filename = _normalizeFilename(reqModel[FIELD_FILENAME])
    data = reqModel[FIELD_DATA]
    truncate = reqModel.get(FIELD_TRUNCATE, False)

    try:
        decoded = ubinascii.a2b_base64(data)
    except Exception as e:
        return _sendResponse(tx=tx, rawResp=_generateErrorResponse(req=REQ_WRITE_FILE, msg=f"Invalid base64 data: [{e}]"))

    try:
        mode = "wb" if truncate else "ab"
        with open(filename, mode) as f:
            f.write(decoded)
        log.info(__name__, f"write_file [{filename}] {'truncate' if truncate else 'append'} {len(decoded)} bytes")
        _sendResponse(tx=tx, rawResp=_generateResponse(req=REQ_WRITE_FILE, values={FIELD_WRITTEN: len(decoded), FIELD_SIZE: util.file_size(filename)}))
    except Exception as e:
        return _sendResponse(tx=tx, rawResp=_generateErrorResponse(req=REQ_WRITE_FILE, msg=f"Failed to write file: [{e}]"))


def _getFileHash(tx: aioble.Characteristic, reqModel: dict):
    """
    Return the MD5 hex digest of a file's contents.
    """
    if FIELD_FILENAME not in reqModel:
        return _sendResponse(tx=tx, rawResp=_generateErrorResponse(req=REQ_FILE_HASH, msg=f"Missing Json Field [{FIELD_FILENAME}]"))

    filename = _normalizeFilename(reqModel[FIELD_FILENAME])

    if not util.file_exists(filename):
        return _sendResponse(tx=tx, rawResp=_generateErrorResponse(req=REQ_FILE_HASH, msg=f"File not found: [{filename}]"))

    try:
        h = util.file_hash(filename)
        _sendResponse(tx=tx, rawResp=_generateResponse(req=REQ_FILE_HASH, values={FIELD_HASH: h}))
    except Exception as e:
        _sendResponse(tx=tx, rawResp=_generateErrorResponse(req=REQ_FILE_HASH, msg=f"Failed to hash file: [{e}]"))


def _deleteFile(tx: aioble.Characteristic, reqModel: dict):
    """
    Delete a file from the filesystem.
    """
    if FIELD_FILENAME not in reqModel:
        return _sendResponse(tx=tx, rawResp=_generateErrorResponse(req=REQ_DELETE_FILE, msg=f"Missing Json Field [{FIELD_FILENAME}]"))

    filename = _normalizeFilename(reqModel[FIELD_FILENAME])

    try:
        if util.file_delete(filename):
            log.info(__name__, f"delete_file [{filename}]")
            _sendResponse(tx=tx, rawResp=_generateResponse(req=REQ_DELETE_FILE))
        else:
            _sendResponse(tx=tx, rawResp=_generateErrorResponse(req=REQ_DELETE_FILE, msg=f"File not found: [{filename}]"))
    except Exception as e:
        _sendResponse(tx=tx, rawResp=_generateErrorResponse(req=REQ_DELETE_FILE, msg=f"Failed to delete file: [{e}]"))


async def _processRequest(rawReq: str, tx: aioble.Characteristic, deviceName: str, deviceInfo: dict = {}) -> bool:
    """
    Take the raw string json request, process the command, and return
    a json model as a raw string.
    Return TRUE when a `complete` request is processed.  False for all else.
    """
    reqModel = json.loads(rawReq)

    if reqModel is None:
        _sendResponse(tx, _generateErrorResponse(req=None, msg="Received Empty Request"))
        return False

    if FIELD_REQ not in reqModel:
        _sendResponse(tx, _generateErrorResponse(req=None, msg=f"Missing [{FIELD_REQ}]"))
        return False

    req = reqModel[FIELD_REQ]

    if req == REQ_GET_DEVICE_INFO:
        _sendResponse(
            tx=tx,
            rawResp=_generateResponse(
                req=req,
                values={FIELD_DEVICE_NAME: deviceName} | deviceInfo
            )
        )
        return False

    if req == REQ_CONNECT_TO_WIFI:
        _attemptConnectWifi(tx=tx, reqModel=reqModel)
        return False

    if req == REQ_GET_AVAILABLE_WIFI:
        _sendAvailableWifiResponse(tx)
        return False

    if req == REQ_COMPLETE:
        _sendResponse(tx, _generateResponse(req=req))
        await asyncio.sleep(0.2)
        return True

    if req == REQ_WRITE_FILE:
        _writeFile(tx=tx, reqModel=reqModel)
        return False

    if req == REQ_FILE_HASH:
        _getFileHash(tx=tx, reqModel=reqModel)
        return False

    if req == REQ_DELETE_FILE:
        _deleteFile(tx=tx, reqModel=reqModel)
        return False

    _sendResponse(tx, _generateErrorResponse(req=req, msg="Unknown Request"))
    return False
