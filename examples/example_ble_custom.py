import uasyncio as asyncio
from uwifisetup import ble


async def customHandler(reqDict: dict) -> bool | None:
    req = reqDict.get('req')

    if req == 'ping':
        ble.send({'resp': 'ping', 'resp_code': 'ok', 'msg': 'pong'})
        return True

    if req == 'info':
        ble.send({'resp': 'info', 'resp_code': 'ok', 'version': '1.0'})
        return True

    if req == 'shutdown':
        ble.send({'resp': 'shutdown', 'resp_code': 'ok'})
        ble.stop()
        return True

    return False


async def main():
    print("Starting custom BLE UART service...")
    await ble.startUART(
        deviceName="CustomBLE",
        handler=customHandler
    )
    print("BLE UART stopped.")


asyncio.get_event_loop().run_until_complete(main())
print("Done.")
