import uasyncio as asyncio  # type:ignore [import-untyped, import-not-found]
import ubluetooth as bluetooth  # type:ignore [import-not-found]
import aioble  # type:ignore [import-not-found]
import json
from micropython import const  # type:ignore [import-not-found]
from . import log

FIELD_RESP = 'resp'
FIELD_RESP_CODE = 'resp_code'
FIELD_MSG = 'msg'

CODE_OK = 'ok'
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

_txChar: aioble.Characteristic = None  # type:ignore [assignment]
_shutdownEvent = asyncio.Event()
_rxBuffer = ""


async def _defaultHandler(reqModel: dict) -> bool | None:
    """
    Default BLE UART handler — does nothing. Override with your own.

    Use `ble.send(response_dict)` to send responses.
    Use `ble.stop()` to shut down the service.

    Return True (or None) if you handled the request.
    Return False if you did not (ble.py will log a warning).

    req is the string req in the json body
    repModel is every other field (including the req field) in a dict
    """
    return None


async def startUART(
        deviceName: str,
        advertiseAppearance: int = _GENERIC_COMPUTER,
        handler=_defaultHandler):
    """
    Start a BLE Nordic UART service and listen for JSON requests.

    `deviceName`: Name advertised in BLE scan.

    `advertiseAppearance`: BLE appearance icon (default generic computer).

    `handler`: Async function called with parsed JSON request dict.
        Signature: async def myHandler(reqModel: dict) -> bool | None
        Use `ble.send(response_dict)` to send responses.
        Use `ble.stop()` to shut down the UART service.
        Return True (or None) if handled, False if not.
    """

    assert deviceName is not None, "deviceName is required"
    assert isinstance(deviceName, str), "deviceName must be a string"
    assert advertiseAppearance is not None, "advertiseAppearance is required"
    assert isinstance(advertiseAppearance, int), "advertiseAppearance must be an int"

    global _txChar
    global _rxBuffer

    log.info(__name__, f"Starting BLE UART [{deviceName}]")

    _shutdownEvent.clear()

    uartService = aioble.Service(_UART_UUID)
    txChar = aioble.Characteristic(uartService, _UART_TX, read=True, notify=True)
    rxChar = aioble.Characteristic(uartService, _UART_RX, write=True, capture=True)

    rxChar.write(bytearray(256))

    genericService = aioble.Service(_GENERIC_ACCESS)
    defaultName = aioble.Characteristic(genericService, _DEVICE_NAME, read=True, notify=True)
    defaultName.write(deviceName)

    aioble.register_services(genericService, uartService)

    _txChar = txChar

    while not _shutdownEvent.is_set():

        async with await aioble.advertise(interval_us=_ADV_INTERVAL_US,
                                          name=deviceName,
                                          services=[_UART_UUID, _GENERIC_ACCESS],
                                          appearance=advertiseAppearance) as connection:

            if _shutdownEvent.is_set():
                break

            log.info(__name__, f"Connected from {connection.device}")
            _rxBuffer = ""

            while connection.is_connected() and not _shutdownEvent.is_set():

                try:
                    con, data = await rxChar.written(timeout_ms=1000)
                    rawData = data.decode()
                    trigger = _RX_TRIGGER_CHAR in rawData

                    if trigger:
                        rawData = rawData.split(_RX_TRIGGER_CHAR, 1)[0]

                    _rxBuffer += rawData
                    _rxBuffer = _rxBuffer.strip()

                    if len(_rxBuffer) > _MAX_BUFFER_SIZE:
                        errorMessage = f"RX buffer overflow ({len(_rxBuffer)} bytes), flushing"
                        log.error(__name__, errorMessage)
                        if connection.is_connected():
                            send(_makeErrorResponse(req=None, msg=errorMessage))
                        _rxBuffer = ""
                    elif len(_rxBuffer) == 0:
                        errorMessage = "Empty Request Received, ignored"
                        log.error(__name__, errorMessage)
                        if connection.is_connected():
                            send(_makeErrorResponse(req=None, msg=errorMessage))
                        _rxBuffer = ""
                    elif trigger:
                        log.info(__name__, f"rx: {_rxBuffer}")

                        reqModel = None
                        try:
                            reqModel = json.loads(_rxBuffer)
                        except Exception as e:
                            log.error(__name__, f"JSON parse error: {e}")
                            if connection.is_connected():
                                send(_makeErrorResponse(req=None, msg=f"Invalid JSON: {e}"))
                            _rxBuffer = ""

                        if reqModel is not None and handler is not None:
                            handled = await handler(reqModel)
                            if handled is False:
                                log.warn(__name__, f"Handler did not handle request: {reqModel}")

                        _rxBuffer = ""
                except asyncio.TimeoutError:
                    _rxBuffer = ""
                except Exception as e:
                    _rxBuffer = ""
                    log.error(__name__, "Unexpected Error", ex=e)
                    if connection.is_connected():
                        send(_makeErrorResponse(req=None, msg=f"Unexpected Error: {type(e).__name__}: {e}"))

                await asyncio.sleep_ms(10)

            log.info(__name__, "Connection Lost")

    log.info(__name__, "BLE UART stopped")


def makeResponse(req: str, values: dict | None = None, code: str = CODE_OK) -> dict:
    """
    Make a generic response message to be sent via the send() function
    """
    resp = {}
    resp[FIELD_RESP] = req
    resp[FIELD_RESP_CODE] = code

    if values is not None:
        resp = resp | values

    return resp


def makeErrorResponse(req: str | None, msg: str) -> dict:
    """
    Make an error resposne to be sent over the send() function
    """
    resp = {}
    resp[FIELD_RESP] = req or "ERR"
    resp[FIELD_RESP_CODE] = CODE_ERROR
    resp[FIELD_MSG] = msg
    return resp


def send(responseDict: dict):
    """
    Send a JSON response over the BLE UART TX channel.

    `responseDict`: A dict that will be wrapped with resp/resp_code fields
        and sent as a JSON string. If the dict already contains 'resp' and
        'resp_code', they are preserved. Otherwise defaults are added.
    """
    if 'resp' not in responseDict:
        responseDict['resp'] = ''
    if 'resp_code' not in responseDict:
        responseDict['resp_code'] = CODE_OK

    rawResp = json.dumps(responseDict)
    log.info(__name__, f"tx: {rawResp}")
    rawResp += '\r\n'
    _txChar.write(data=rawResp, send_update=True)


def stop():
    """
    Signal the BLE UART service to shut down.
    Causes startUART to exit its loop and return.
    """
    _shutdownEvent.set()


def _makeErrorResponse(req: str | None, msg: str) -> dict:
    resp = {}
    resp[FIELD_RESP] = req or "ERR"
    resp[FIELD_RESP_CODE] = CODE_ERROR
    resp[FIELD_MSG] = msg
    return resp
