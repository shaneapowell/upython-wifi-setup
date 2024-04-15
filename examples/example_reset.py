import uasyncio as asyncio
from uwifisetup import wifi


async def main():

    wifi.factoryReset()



asyncio.get_event_loop().run_until_complete(main())
