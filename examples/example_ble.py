import uasyncio as asyncio
from uwifisetup import wifi


async def main():

    deviceName = "MyUPy"

    # Setup / Connect to Wifi
    if wifi.hasCredentials():
        if await wifi.connectWifi(deviceName):
            print("Connected to wifi Success")
        else:
            print("WiFi Connect failure. Reset to try again.")
            # The esp32 wifi can get "stuck" for some reason I'm not quite sure of. resetting the device fixes this most times.
            import machine
            machine.reset()
    else:
        from uwifisetup import blesetup
        await blesetup.setupWifi(deviceName="MyPyDevice",
                                 deviceInfo={"uuid": "123456"},
                                 resetDeviceWhenSetupComplete=True)


asyncio.get_event_loop().run_until_complete(main())
print("Done...")