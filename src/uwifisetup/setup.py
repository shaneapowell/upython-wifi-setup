from microdot_asyncio import Microdot, send_file, redirect, Response
from microdot_utemplate import render_template, init_templates
from utemplate import source, recompile
import uasyncio as asyncio
import network
import machine
import socket
import os, time, sys, gc
import uwifisetup.wifi as wifi
import uwifisetup.log as log
import uwifisetup.util as util

DEFAULT_FILE_ROOT = "www"
PORTAL_IP = '172.18.4.1'
PORTAL_MASK = '255.255.255.0'

MIME = {
    "default": "text/plain",
    ".css": "text/css",
    ".ico": "image/vnd.microsoft.icon",
    ".jpg": "image/jpeg",
    ".png":  "image/png",
    ".svg": "image/svg+xml"
}

_wifi = network.WLAN(network.STA_IF)
_portal = None
_dnsServerRunning = True


APP_NAME="AppName Here"
APP_VERSION="1.2.3a"

async def setupWifi(deviceName, templateFileRoot = DEFAULT_FILE_ROOT, resetDeviceWhenSetupComplete = False):
    """
    Run the setup portal websever and capture dns server.
    This is done in an async, so you must await this. The
    response is True if the setup was a success. False if it
    was a failure for some reason. Though, at this point in the
    design of this class, I don't know what that could be.
    The portal will remain active until a wifi is correctly configured.
    """
    global _dnsServerRunning

    assert deviceName is not None, "deviceName is required"
    assert isinstance(deviceName, str), "deviceName must be a string"
    assert templateFileRoot is not None, "template file root is requried"
    assert isinstance(templateFileRoot, str), "template root must be a string"
    assert resetDeviceWhenSetupComplete is not None, "resetDeviceWhenSetupComplete is requried"
    assert isinstance(resetDeviceWhenSetupComplete, bool), "resetDeviceWhenSetupComplete must be a bool"

    log.info(__name__, f"Starting WiFi Setup [{deviceName}]")

    network.hostname(deviceName)
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.ifconfig((PORTAL_IP, PORTAL_MASK, PORTAL_IP, PORTAL_IP))
    ap.config(essid=deviceName, authmode=network.AUTH_OPEN)
    log.info(__name__, f"AP IP Conf {ap.ifconfig()}")


    # Run the portal, and wait for it
    dnsTask = asyncio.create_task(_startDnsServer())
    await _startPortalWebServer(templateFileRoot=templateFileRoot)

    # Shutdown the DNS service. The dns will get a AP DOWN exception when we shut down the ap below
    _dnsServerRunning = False

    log.info(__name__, "AP is running. Shutting down.")
    ap.disconnect()
    ap.active(False)
    ap = None

    log.info(__name__, f"Wifi Portal Copmplete... reset device [{resetDeviceWhenSetupComplete}]")
    if resetDeviceWhenSetupComplete:
        machine.reset()

    shutdown()



def shutdown():
    """
    If the portal was started, shut it down.
    Stop the dns server, and shutdown the web portal server.
    This is automatically called at the end of the wifi setup
    stages. not needed to be called manually.
    """
    log.info(__name__, "Shutting Down Captive Portal")
    global _portal

    if _portal:
        log.info(__name__, "Portal Server is running. Shutting down.")
        _portal.shutdown()
        _portal = None


async def _startDnsServer():
    """
    Fire up the async dns server.  task.cancel() top shut this down.
    """
    global _dnsServerRunning

    log.info(__name__, f"Start Captive DNS Server...")

    # Setup our DNS listening socket
    dnsSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dnsSocket.setblocking(False)
    dnsSocket.bind((PORTAL_IP, 53))

    _dnsServerRunning = True
    while _dnsServerRunning:
        try:
            gc.collect()
            #data, rAddr = dnsSocket.recvfrom(4096)
            data, rAddr = dnsSocket.recvfrom(512)
            log.info(__name__, f"Received DNS message ...")
            query = _DNSQueryWrapper(data)
            dnsSocket.sendto(query.response(PORTAL_IP), rAddr)
            await asyncio.sleep_ms(100)

        except Exception as e:
            # Timeout, just keep retrying forever
            await asyncio.sleep(3)

    log.warn(__name__, "DNS server stopped.")
    dnsSocket.close()


async def _startPortalWebServer(templateFileRoot):
    """
    Start up the async microdot server to serve up our captive portal pages.
    Pass in an already setup and configured AccessPoint Interface Instance
    network.
    """
    global _portal

    log.info(__name__, f"Start Captive Portal Server [{templateFileRoot}]...")

    _portal = Microdot()
    Response.default_content_type = 'text/html'
    # init_templates(template_dir=FILE_ROOT, loader_class=recompile.Loader)
    # init_templates(template_dir=FILE_ROOT, loader_class=source.Loader)
    init_templates(template_dir=templateFileRoot)

    # Return an "as needed" generator to our template.
    # The scan won't run until teh page is loading, and will
    # iterate the result back with the yields
    # (ssid, bssid, channel, RSSI, authMode, hidden )
    # We'll return only the (SSID, RSSI, AuthType)
    def _networksGen():
        global _wifi
        _wifi.active(True)
        log.info(__name__, "Scanning for available wifi networks...")
        scanResult = [ (n[0].decode(), n[3], n[4]) for n in _wifi.scan() if n[5] is False and len(n[0]) > 0]
        scanResult.sort(key=lambda r: r[1], reverse=True) # Sort by RSSI
        log.info(__name__, f"Wifi Scan Result: [{scanResult}]")
        uniqueNames = set()
        for n in scanResult:
            if n[0] not in uniqueNames:
                uniqueNames.add(n[0])
                yield n


    @_portal.route('/_uwifisetup/welcome.html', methods=['GET','POST'])
    async def getWelcome(request):
        """
        Stage 1.
        The main welcome screen.
        Instructions, and the "setup wifi" button
        """
        return render_template(
            template=request.path,
            appName=APP_NAME,
            appVersion=APP_VERSION
        )


    @_portal.route('/_uwifisetup/list_networks.html', methods=['GET','POST'])
    async def getListNetworks(request):
        """
        Stage 2.
        List the visible WiFi access points.
        """
        log.info(__name__, "Network List Result\n")
        return render_template(
            template=request.path,
            appName=APP_NAME,
            appVersion=APP_VERSION,
            networksGen=_networksGen
        )


    @_portal.route('/_uwifisetup/try_connect.html', methods=['GET', 'POST'])
    async def tryConnect(request, message=None):
        """
        Stage 3.
        Enter the creds for the wifi access point we want to join.
        Attempt a connection, return here the result.
        """
        attemptConnect = False

        # The GET is coming from the previous network list page
        if request.method == 'GET':
            ssid = request.args['ssid']
        else:
            # Post should be connection attempt request
            ssid = request.form.get("ssid")
            password = request.form.get("password")
            attemptConnect = True

        def connectFunction():
            """
            A per-attempt callback function to attempt to connect to the indicated wifi.
            Returns a tuple with the (bool:success, str:message) values.
            """
            global _wifi
            _wifi.active(True)
            log.info(__name__, f"Attempting to connect WiFi to [{ssid}]")

            success = False
            if ssid is None or len(ssid) <= 0:
                message = "Invalid SSID"
            elif attemptConnect:

                try:
                    # Attempt connection ...
                    if _wifi.isconnected():
                        _wifi.disconnect()
                    _wifi.connect(ssid, password)

                    # Wait for the connection. We'll timeout after 10 seconds.
                    result = None
                    sleepTime = 0
                    while True:
                        time.sleep(0.5)
                        result = _wifi.status()
                        if result != network.STAT_CONNECTING:
                            break;
                        sleepTime += 1
                        if sleepTime >= 20:
                            sleepTime = -1
                            break;

                    if sleepTime == -1:
                        message = "Timed Out"
                    else:
                        if result == network.STAT_GOT_IP:
                            success = True
                            message = f"Success\n({_wifi.ifconfig()[0]})"
                            wifi.saveCredentials(ssid, password)
                        elif result == network.STAT_WRONG_PASSWORD:
                            message = "Password Error"
                        elif result == network.STAT_NO_AP_FOUND:
                            message = "WiFi not in range"
                        else:
                            message = "General Error"
                except Exception as e:
                    log.info(__name__, f"Unexpected Exception connecting to wifi {e}")
                    message = str(e)

            log.info(__name__, f"Connect to [{ssid}] = {success} - {message}")
            return (success, message)

        cf = connectFunction if attemptConnect else None
        return render_template(
            template=request.path,
            appName=APP_NAME,
            appVersion=APP_VERSION,
            ssid=ssid,
            connectFunc=cf
        )


    @_portal.route('/_uwifisetup/complete.html', methods=['GET','POST'])
    async def getComplete(request):
        """
        Stage 4.
        All done.   What to do next. etc.
        Continue to reboot.
        """
        global _wifi
        return render_template(
            template=request.path,
            appName=APP_NAME,
            appVersion=APP_VERSION,
            ipAddress=_wifi.ifconfig()[0]
        )


    @_portal.route('/_uwifisetup/setup_complete', methods=['GET'])
    async def setupComplete(request, message=None):
        """
        Reboot the device
        """
        log.info(__name__, "Setup Complete...")
        shutdown()
        return "stopping...", 200


    @_portal.route('/_uwifisetup/assets/<asset>')
    async def getAssets(request, asset):
        """
        All non-template Static Asset content
        """
        log.info(__name__, f"Request for asset [{request.path}]")

        if '..' in asset:
            # directory traversal is not allowed
            return 'Not found', 404

        file = f"{templateFileRoot}{request.path}"

        contType = MIME['default']
        for k,v in MIME.items():
            if file.endswith(k):
                contType = v
                break

        compressed = False
        gzfile = f"{file}.gz"

        if util.file_exists(gzfile):
            file = gzfile
            compressed = True

        if not util.file_exists(file):
            log.warn(__name__, f"File Not Found [{file}] -> 404")
            return "Not Found", 404

        log.debug(__name__, f"Returning with file [{file}] [{contType}]")
        return send_file(file, content_type=contType, compressed=compressed, max_age=3600)


    @_portal.route('/<path>')
    async def getCaptured(request, path):
        log.info(__name__, f"request for [{path}]")

        # Default, is to redirect on every unknown request
        log.info(__name__, "Redirecting to welcome Page")
        return redirect('/_uwifisetup/welcome.html')


    # **************************
    # Lastly, start up the server
    await _portal.start_server(port=80, debug=True)
    log.info(__name__, "Captive Portal Server Stopped")


class _DNSQueryWrapper:
    def __init__(self, data):
        self.data = data
        self.domain = ''
        tipo = (data[2] >> 3) & 15  # Opcode bits
        if tipo == 0:  # Standard query
            ini = 12
            lon = data[ini]
            while lon != 0:
                self.domain += data[ini + 1:ini + lon + 1].decode('utf-8') + '.'
                ini += lon + 1
                lon = data[ini]

    def response(self, ip):
        log.info(__name__, f"DNS Query {self.domain} -> {ip}")
        if self.domain:
            packet = self.data[:2] + b'\x81\x80'
            packet += self.data[4:6] + self.data[4:6] + b'\x00\x00\x00\x00'  # Questions and Answers Counts
            packet += self.data[12:]  # Original Domain Name Question
            packet += b'\xC0\x0C'  # Pointer to domain name
            packet += b'\x00\x01\x00\x01\x00\x00\x00\x3C\x00\x04'  # Response type, ttl and resource data length -> 4 bytes
            packet += bytes(map(int, ip.split('.')))  # 4bytes of IP
        return packet