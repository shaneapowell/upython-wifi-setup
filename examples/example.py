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
        from uwifisetup import setup
        await setup.setupWifi(deviceName="MyPyDevice",
                              appName="My App",
                              welcomeMessage="Time to setup your device WiFi",
                              completeMessage="Your device will now restart. You may access your device with your webbrowser on your phone or laptop",
                              resetDeviceWhenSetupComplete=True)


asyncio.get_event_loop().run_until_complete(main())
print("Done...")