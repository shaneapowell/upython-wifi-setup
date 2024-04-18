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
                    resetDeviceWhenSetupComplete: bool = False)
```

Run the setup portal websever and capture dns server.
This is done in an async, so you must await this.

deviceName: is the title put at the top of the welcome page on the portal
tempalteFileRoot: is the location of the _uwifisetup html and assets files. The default is in the directory `www` on the device.
resetDeviceWhenSetupComplete: Due to memory limitation, it is wise to reset this device after the setup is complete to free up resources.

<a id="uwifisetup.setup.shutdown"></a>

#### shutdown

```python
def shutdown()
```

If the portal was started, shut it down.
Stop the dns server, and shutdown the web portal server.
This is automatically called at the end of the wifi setup
stages. not needed to be called manually.

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
result in a "setup" stage being started.

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

<a id="uwifisetup.wifi.connectWifi"></a>

#### connectWifi

```python
async def connectWifi(deviceName) -> bool
```

Attemmpt to Connect to the configure wifi, assuming a config has been
setup. This will always return success if a wifi has been configure, becuase
the attempts to connect will continue indefinitly.
However, if no credentials are yet setup, this will return a False.
The connection status of the wifi is obtainable from the _wifi
instance via self.getWifi() function.

