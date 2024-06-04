from . import log
from uwifisetup import wifi
import uasyncio as asyncio  # type:ignore [import-untyped]
import ubluetooth as bluetooth  # type:ignore [import-not-found]
import aioble  # type:ignore [import-not-found]
import json
import network   # type:ignore [import-not-found]
import time
import machine  # type:ignore [import-not-found]
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

REQ_GET_DEVICE_INFO = 'get_device_info'
REQ_GET_AVAILABLE_WIFI = 'get_available_wifi'
REQ_CONNECT_TO_WIFI = 'connect_to_wifi'
REQ_COMPLETE = 'complete'

CODE_OK = 'ok'
CODE_DONE = 'done'
CODE_ERROR = 'error'

_GENERIC_ACCESS = bluetooth.UUID(0x1800)
_DEVICE_NAME = bluetooth.UUID(0x2A00)
_DEVICE_APPEARANCE = bluetooth.UUID(0x2A01)
_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_RX = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
_GENERIC_COMPUTER = const(0x002)
_ADV_INTERVAL_US = const(250000)

_wlan = network.WLAN(network.STA_IF)



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
    aioble.register_services(uartService)

    # Override the mpy default device-name characteristic. This seems to work, but if you
    # inspect the BLE device , it shows the 0x1800 primary service twice.
    # Seems that this doesn't overwrite the built-in service, but instead adds a 2nd one
    genericService = aioble.Service(_GENERIC_ACCESS)
    defaultName = aioble.Characteristic(genericService, _DEVICE_NAME, read=True, notify=True)
    defaultName.write(deviceName)
    aioble.register_services(genericService)

    isComplete = False

    while not isComplete:

        async with await aioble.advertise(interval_us=_ADV_INTERVAL_US,
                                          name=deviceName,
                                          services=[_UART_UUID, _GENERIC_ACCESS],
                                          appearance=advertiseAppearance) as connection:

            log.info(__name__, f"Connection from {connection.device}")

            while connection.is_connected():

                try:
                    con, data = await rxChar.written(timeout_ms=1000)
                    rawReq = data.decode()
                    log.info(__name__, f"rx: {rawReq}")
                    isComplete = await _processRequest(
                        rawReq=rawReq,
                        tx=txChar,
                        deviceName=deviceName,
                        deviceInfo=deviceInfo)
                    if isComplete:
                        await connection.disconnect()
                except asyncio.TimeoutError:
                    # We dont' really care. Just need a away to not hold us up if the connection closes
                    pass
                except Exception as e:
                    log.error(__name__, "Unexpected Error", ex=e)
                    if connection.is_connected():
                        _sendResponse(tx=txChar, rawResp=_generateErrorResponse(req=None, msg="Unexpected Error"))


                asyncio.sleep_ms(10)

    log.info(__name__, f"BLE WiFi Setup Complete... reset device [{resetDeviceWhenSetupComplete}]")
    if resetDeviceWhenSetupComplete:
        machine.reset()


def _sendResponse(tx: aioble.Characteristic, rawResp: str):
    """
    A simple send function to be shared
    """
    log.info(__name__, f"tx: {rawResp}")
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

    _sendResponse(tx, _generateErrorResponse(req=req, msg="Unknown Request"))
    return False
