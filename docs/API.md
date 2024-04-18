# Table of Contents

* [uwifisetup](#uwifisetup)
* [uwifisetup.log](#uwifisetup.log)
* [uwifisetup.setup](#uwifisetup.setup)
  * [setupWifi](#uwifisetup.setup.setupWifi)
  * [shutdown](#uwifisetup.setup.shutdown)
* [uwifisetup.util](#uwifisetup.util)
* [uwifisetup.wifi](#uwifisetup.wifi)
  * [hasCredentials](#uwifisetup.wifi.hasCredentials)
  * [factoryReset](#uwifisetup.wifi.factoryReset)
  * [saveCredentials](#uwifisetup.wifi.saveCredentials)
  * [loadCredentials](#uwifisetup.wifi.loadCredentials)
  * [getWifi](#uwifisetup.wifi.getWifi)
  * [connectWifi](#uwifisetup.wifi.connectWifi)

<a id="uwifisetup"></a>

# uwifisetup

<a id="uwifisetup.log"></a>

# uwifisetup.log

<a id="uwifisetup.setup"></a>

# uwifisetup.setup

<a id="uwifisetup.setup.setupWifi"></a>

#### setupWifi

```python
async def setupWifi(deviceName: str,
                    appName: str,
                    welcomeMessage: str,
                    completeMessage: str,
                    templateFileRoot: str = DEFAULT_FILE_ROOT,
                    resetDeviceWhenSetupComplete: bool = False,
                    usePreCompiledTemplates: bool = True)
```

Run the setup portal websever and capture dns server.
This is done in an async, so you must await this.

deviceName`: What  you'll see broadcast as the available Access Point Name

`appName`: is the title put at the top of the welcome page on the portal.

`welcomeMessage`: the text to put onto the welcome page.

`completeMessage`: the text to put on the final complete page.

`templateFileRoot`: is the location of the _uwifisetup html and assets files. The default is in the directory `www` within this deployment package.
    If you decide to move where the assets are contained, or which to modify them and use different assets, you can specify the final location with this
    parameter. This is especially necessary if you decide to `freeze` all your code and dependencies in a custom build firmware. Asset files must remain
    on the main data filesystem.

`usePreCompiledTemplates`: indicates to the utemplate engine that the template files are already built into .py or .mpy files.  Therefor, use the
    `compiled` loader.  Set this to `False` to use the `source` loader. Which will attempt to find the raw `*.html` template files, and real-time compile
    them into the appropriate .py file.  If you are using custom templates for this library, you might want to set this to False.

resetDeviceWhenSetupComplete: Due to memory limitation, it is wise to reset this device after the setup is complete to free up resources.

<a id="uwifisetup.setup.shutdown"></a>

#### shutdown

```python
def shutdown()
```

If the portal was started, shut it down.
Stop the dns server, and shutdown the web portal server.
This is automatically called at the end of the wifi setup
stages. Not needed to be called manually.

<a id="uwifisetup.util"></a>

# uwifisetup.util

<a id="uwifisetup.wifi"></a>

# uwifisetup.wifi

<a id="uwifisetup.wifi.hasCredentials"></a>

#### hasCredentials

```python
def hasCredentials() -> bool
```

return the credentials status. If the setup has run,
we'll have valid credentails on hand.  return True
If not, .. well.. we won't. return False

<a id="uwifisetup.wifi.factoryReset"></a>

#### factoryReset

```python
def factoryReset()
```

Purge/Delete the creds file. Which will
result in a "setup" stage being started next time.

<a id="uwifisetup.wifi.saveCredentials"></a>

#### saveCredentials

```python
def saveCredentials(ssid: str, pwd: str)
```

Save the values to the creds file.
line 0 = ssid
line 1 = pwd

<a id="uwifisetup.wifi.loadCredentials"></a>

#### loadCredentials

```python
def loadCredentials() -> tuple[str, str] | None
```

Read the creds from the file.

<a id="uwifisetup.wifi.getWifi"></a>

#### getWifi

```python
def getWifi()
```

Return the singleton wifi instance.
Just a simple clean wrapper around
`network.WLAN(network.STA_IF)`.
Here just for added convenience.

<a id="uwifisetup.wifi.connectWifi"></a>

#### connectWifi

```python
async def connectWifi(deviceName) -> bool
```

Attempt to Connect to the configure wifi, assuming a config has been
setup. This will always return success if a wifi has been configure, because
the attempts to connect will continue indefinitely.
However, if no credentials are yet setup, this will return a False.
The connection status of the wifi is obtainable from the _wifi
instance via self.getWifi() function.  Which is the same as calling `network.WLAN(network.STA_IF)`

