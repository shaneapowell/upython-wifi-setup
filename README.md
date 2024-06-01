# Work In Progress
**This library is still under active development.**

# New Features
- BLE UART Setup

# uPython Wifi Setup
A simple to install setup and use WiFi Setup Portal for micropython based ESP32 boards.


![aplist](docs/sc_aplist.png) ![aplist](docs/sc_password.png)

[All Screenshots](docs/SCREENSHOTS.md)


# Features
Inspired by https://github.com/george-hawkins/micropython-wifi-setup
- Reliable and Simple
- Low Memory Overhead
- ASYNC processing
- Very simple web-browser requirements.  Minimal Javascript.
- No separate web-app build step.  Just simple html template files. Not Fancy, Just Functional.
- Easy to integrate into your existing projects.
- Easy to build your project upon if desired.
- Easy to modify to make it your own.
- **(new)** Bluetooth LE UART Setup Support

# Future Plans
- Self-Installing templates and assets into data directory on device.
- Unit Tests!
- Easier Theming

# Tested On
- SEEED Xaio ESP32-S3
- SEEED Xaio ESP32-C3

# Dependencies
The following 3 libraries are required dependencies.  Recommended you drop these into your `/lib` directory on your device
- [utemplate](https://github.com/pfalcon/utemplate)
  - copy the directory `utemplate` in the repo to `/lib/utemplate` on your device
- [microdot](https://github.com/miguelgrinberg/microdot)
  - copy the directory `src/microdot` to `/lib/microdot` on your device
  - note, Not all microdot files are needed, you can skip the ones you don't want to use yourself. the only required files for this library are:
    - `__init__.py`
    - `microdot.py`
    - `utemplate.py`
- [aioble](https://github.com/micropython/micropython-lib/blob/master/micropython/bluetooth/aioble/README.md) - If you intend to use the `blesetup` module.
  -  `mpremote mip install aioble`

# The Library Contents
Made up of 2 main parts. The .py source files, and the assets.
They are kept separate to simplify customizing this library.

## `uwifisetup` - The source
This is the library python files.  These files need to be in the `/lib` or the `/` root of your device.  Or, pre-frozen in the `modules` directory of a custom micropython firmware.

## `www` - The Assets
This is the assets directory.  Contains the `.html` template files, and a handfull of image and css assets.
These files by default are loaded from `/lib/uwifisetup/www` from your device. That is the default install location using the mip install method below.

If you happen to be building an IOT web-app, then you might wish to modify the portal template and css files to match your desired look-and-feel.  You might also then want to use the same template and asset structure in your main web-app.  Moving the `www` directory and contents to a common location on your device allows you full access and control of the files.

To move these to a different install location on your deivce, you need only specify a different `templateFileRoot` parameter to `setup.setupWifi(...)`.   The simplest thing to do is to move the `www` folder to the root of your micropython filesystem, and pass just `wwww` to the setupWifi function.
```python
await setup.setupWifi(templateFileRoot='www'...)
```
You can now setup your own `microdot` web-server, with your own template files within the `www` directory, and include the `_top.html` and `_bottom.html` and `_start.html` wrapper template files to mimic the look and feel and functionality.  Reference the `welcome.html` and `list_networks.html` for example use.

Simply put, you need to reference any common assets offered up by this wifi setup with the relative path of `uwifisetup/<file>` .
```
{% include "_uwifisetup/_bottom.html" %}
```
or
```
<img class="f-right" src="/_uwifisetup/assets/network_wifi_{{ numBars }}_bar{{ showLock }}_48px.svg"/>
```


# Install (EASIEST)
You'll need [mpremote](https://docs.micropython.org/en/latest/reference/packages.html#installing-packages-with-mpremote) installed on your system.
There are a number of ways to do the install, all platform dependant.
Linux/Mac
```sh
pip install mpremote
```

## MIP (.mpy)
Install `upython-wifi-setup` into `/lib/uwifisetup` on the device.
This installs the `.mpy` pre-compiled versions of this library, but still uses the `*.py` of the dependencies.  For now...
```sh
mpremote mip install aioble
mpremote mip install github:shaneapowell/upython-wifi-setup/package-deps.json
mpremote mip install github:shaneapowell/upython-wifi-setup/package.json
```

## MIP (.py)
You can optionally install the non .mpy original source.
```sh
mpremote mip install aioble --no-mpy
mpremote mip install github:shaneapowell/upython-wifi-setup/package-deps.json
mpremote mip install github:shaneapowell/upython-wifi-setup/package-raw.json
```

## Try It Out!
After doing one of the above install steps.. you can give it a try it out with the following.
Copy the `example.py` file to your local system on your computer, and run it with `mpremote`. Follow the steps to connect to your wifi.
```sh
wget https://raw.githubusercontent.com/shaneapowell/upython-wifi-setup/main/examples/example.py
mpremote run example.py
```

- Re-Run the above example.py file again to then see it connect to your wifi.
- you can reset/clear the `creds.json` file to try it all again.
```sh
mpremote rm /creds.json
```

# Install (Easy)
- Clone this repo
  ```sh
  git clone https://github.com/shaneapowell/upython-wifi-setup.git
  git submodule init
  git submodule update
  ```
- install [pipenv](https://pypi.org/project/pipenv/).
  ```sh
  pip3 install pipenv
  ```
- Plug in your micropython esp32 device usb to your computer.
- Update the `.env` file, set the `RSHELL_PORT` with the TTY path to your device.
- Sync the pipenv venv packages. This is only needed once, or with any new updates to the `Pipfile`.
  ```sh
  pipenv sync
  ```
- Install the [microdot](https://github.com/miguelgrinberg/microdot) and [utemplate](https://github.com/pfalcon/utemplate/) package dependencies into `/lib` on the device
  ```sh
  pipenv run deploy_deps
  ```
- Install the [aioble](https://github.com/micropython/micropython-lib/blob/master/micropython/bluetooth/aioble/README.md) if using the blesetup feature.
  ```sh
  mpremote mip install aioble
  ```
- Optional build the pre-compiled parts. Optional because the `dist` folder should already have the most recent-pre-compiled.
  Note: YOu'll see some like `ModulenotFoundError: No Module named `_uwifisetup/complete_html`. You can safely ignore those.
  ```sh
  pipenv run compile
  ```
- Deploy the code and assets into the `/lib` directory.
  ```sh
  pipenv run deploy
  ```

- Try it Out. Run the example
  ```
  pipenv run example
  ```
- Connect your phone to the wifi access point named `MyPyDevice`
- After the setup is complete, the device should reset itself.
- Re-Run the above example, and the command should finish with a message
  ```
  Connected to wifi Success
  ```
- Re-Run the example now, to see the wifi connect using your new creds
  ```sh
  pipenv run example
  ```
- Re-Set your creds to try all over again
  ```sh
  pipenv run example_reset
  ```

# Install (Manual)
Because you're the type of person who needs to do things manually.  You can inspect the `Pipfile` for commands to reference.
- Manually Install the `microdot` and `utemplate` dependencies.
- Manually copy over the `dist/uwifisetup` (pre-compiled) or `src/uwifisetup` (source) files to `/lib/uwifisetup`.
- Manually copy over the `dist/www` (pre-compiled) or `src/www` (source) files to `/lib/uwifisetup/www`
- if you copied the pre-compiled `dist/www` files, you'll also need to copy over the `src/www/_uwifisetup/assets` files into `/lib/uwifisetup/www/_uwifisetup/assets`


# Pre-Build for Maximum Performance
You can pre-compile the source and template files into .mpy files to reduce the load and overhead on your hardware.   The following will compile and move all distribution files into the `/dist` directory.  You can then deploy the contents of the `/dist` directory, or manually move than as you see fit.
```sh
pipenv run compile
pipenv run deploy
```

# Freeze into a custom firmware
Doing this is a little beyond the scope of this readme.  This is however, what I have done for my projects.  It's a little tricky getting the correct files into the correct directory for a clean deployment.  In short, you want to get all  the `.py` files into the `modules` directory. And all the non `.py` asset files into the filesystem of your device.

The `.py` files are more than just what is in the `src/uwifisetup` directory.  There is also the `.py` files generated by the conversion of the `.html` template files.  These are generated with the `pipenv compile` command, and left in the `src/_uwifisetup/` directory.

I copied the `src/uwifisetup` into the micropython firmware `modules` directory.  I also copied over the `src/www/_uwifisetup/*.py` files. Finally, the non .py files found in the `src/www/_uwifisetup` directory must be placed into the main filesystem of your device. They cannot be pre-frozen as they are not source files.

# Credentials
The access point name, and wifi password are stored in a plain text json file `creds.json` in the root of the data partition.

# BLE UART Mode
The ability to configure your wifi over BLE Nordic UART has been added.  This feature doesn't include a full UI, but rather a simple json based TX/RX protocol that can be used with your own custom BlueTooth application.
see the `example_ble.py`. A very basic json based async protocol is implemented with a few very specific request
commands to handle setting up your wifi.

An important limitation to note is that the messages are limited to 256 characters max. This should not pose a problem for a typical use-case of this protocol.

To play with BLE Uart mode, the mobile app `nRF Toolbox` in the [App Store](https://apps.apple.com/us/app/nrf-toolbox/id820906058) / [Play Store](https://play.google.com/store/apps/details?id=no.nordicsemi.android.nrftoolbox&hl=en_US&gl=US) can be used to send and receive messages.

## Request / Response
A request json must include at a minimum a `req` field with a known request command code.  Each request code has it's own set of optional and required additional fields.

A response for a request will have the request code echoed back, as well as a response code to indicate the outcome of the request, and any additional information specific to the request.

While the module is async, a request will return a response before another request is accepted.  With the echo-back field of the response model, this protocol has the appearance of being totally async, but it is not.  It is semi-blocking sequential.  Semi-Blocking since the network calls themselves are blocking.

### Response codes
- `ok`:  You expect a valid set of fields in the json for the given request.
- `error`: An error was triggered. see the included `msg` field for more info.
- `done`: A response code unique to the `get_available_wifi` command. These are returned one at a time. The last one is empty with this response code.


### Request: `get_device_info`
#### Request
```json
{"req": "get_device_info"}
```
#### Response
Will include the `deviceName` provided to the blesetup.setupWifi() function, and the `deviceInfo` dict values.
```json
{"resp": "get_device_info", "resp_code": "ok", "device_name": "MyPyDevice", "uuid": "123456"}
```

### Request: `get_available_wifi`
Due to the 256 character limit of the UART characteristic, the request will return a series of wifi response models until a status code of `done` is returned.  You'll need to loop on the responses until the `done` status code.  The wifi responses are returned in order from strongest to weakest by default.

#### Request
```json
{"req": "get_available_wifi"}
```

#### Response
Expected Response Fields:
- `ssid` - The STRING SSID of wifi
- `rssi` - The INT RSSI strength of the wifi
- `secure` - The INT code of the type of security of this wifi.  see the ESP32 WLAN `scan` function for expected values.
  - 0 = Open
  - 1 = WEP
  - 2 = WPA-PSK
  - 3 = WPA2-PSK
  - 4 = WPA/WPA2-PSK
```json
{"resp": "get_available_wifi", "resp_code": "ok", "ssid": "My Wifi", "rssi": -71, "secure": 4}
```
```json
{"resp": "get_available_wifi", "resp_code": "ok", "ssid": "Bobs Wifi", "rssi": -56, "secure": 4}
```
```json
{"resp": "get_available_wifi", "resp_code": "ok", "ssid": "Janes Public", "rssi": -46, "secure": 0}
```
```json
{"resp": "get_available_wifi", "resp_code": "done"}
```


### Request: `connect_to_wifi`
Request to connect to a wifi.
The `ssid` and `password` fields are both required, even for an open wifi.  If you are connecting to an unsecure open wifi, just pass a null password value.
#### Request (protected)
```json
{"req": "connect_to_wifi", "ssid": "My Wifi", "password": "abc123"}
```
#### Request (open)
```json
{"req": "connect_to_wifi", "ssid": "My Wifi", "password": null}
```

#### Response
A success response will include your assigned IP address.
```json
{"resp": "connect_to_wifi", "resp_code": "ok", "ip_addr": "192.168.0.142"}
```

Connection Failures will look like
```json
{"resp": "connect_to_wifi", "resp_code": "error", "msg": "Incorrect Password"}
```

### Request: `complete`
Send the `complete` request, to tell the blesetup system to shutdown and fall out of the await. If the blesetup function included `resetDeviceWhenSetupComplete=True`, then this call will result in the device being reset.

### Request
```json
{"req": "complete"}
```

### Response
```json
{"resp": "complete", "resp_code": "ok"}
```

## Try it out with
```
pipenv run example_ble
```


### Example Message Sequence
Plug in the values to match your local wifi, but you can try this sequence with the uRF toolbox mobile app.
```json
TX:{"req": "get_device_info"}
RX:{"resp": "get_device_info", "resp_code": "ok", "device_name": "MyPyDevice", "uuid": "123456"}

TX:{"req": "get_available_wifi"}
RX:{"resp": "get_available_wifi", "resp_code": "ok", "ssid": "My Wifi", "rssi": -71, "secure": 4}
RX:{"resp": "get_available_wifi", "resp_code": "ok", "ssid": "Bobs Wifi", "rssi": -56, "secure": 4}
RX:{"resp": "get_available_wifi", "resp_code": "ok", "ssid": "Janes Public", "rssi": -46, "secure": 0}
RX:{"resp": "get_available_wifi", "resp_code": "done"}

TX:{"req": "connect_to_wifi", "ssid": "My Wifi", "password": "Bad Password"}
RX:{"resp": "connect_to_wifi", "resp_code": "error", "msg": "Timed Out"}
TX:{"req": "connect_to_wifi", "ssid": "My Wifi", "password": null}
RX:{"resp": "connect_to_wifi", "resp_code": "error", "msg": "Unable to Connect"}
TX:{"req": "connect_to_wifi", "ssid": "My Wifi", "password": "abc123"}
RX:{"resp": "connect_to_wifi", "resp_code": "ok", "ip_addr": "192.168.0.142"}

TX:{"req": "complete"}
RX:{"resp": "complete", "resp_code": "ok"}
```


##

# Reference
Functions and Use Reference

## `uwifisetup.setup.py`
- setupWifi()
- shutdown()

## `uwifisetup.wifi.py`
- hasCredentials()
- factoryReset()
- saveCredentials()
- loadCredentials()
- connectWifi()
-

# How to incorporate what this library provides into your project
If you are like me, you will want to use this library, but, make it look like your project/theme.
In that case, it'll be simply up to you to modify the `.css` and `.html` files to your needs.  If you wish to just leverage what this library already provides, you can keep the `.css` and `.html` files unmodified, and include them in your own app.

Look at how the `examples/example.py` file runs this wifi setup library.
It only creates the `microdot` webserver instance if it needs to during the `setup` stage.  If you have no need for a webserver in your project, you don't need to do anything.   If however, you wish to also serve up your own content, but use the templates and css provided by this library.  You'll have to do a little work.  But, not as much as you think.

## What to Do
- Move the `www` templates and assets to the device root `/`
- Modify the `setup(...)` function, passing in a new `templateFileRoot='www'` value.
- Add your own html, template and assets to the `www` directory.
- Setup your own microdot web-server to provide access to the html and assets files.
- Include the already, ready-to-go, `_start.html`, `_top.html` and `_bottom.html` template


# Development
- Clone repo
  ```sh
  git clone https://github.com/shaneapowell/upython-wifi-setup.git
  git submodule update
  ```
- Modify `setup.py`. Near the top, Comment out the `DEFAULT_TEMPLATE_LOADER_CLASS=utemplate.compiled.Loader`. Uncomment the `#DEFAULT_TEMPLATE_LOADER_CLASS=utemplate.recompile.Loader` line.
- Deploy dependencies as normal
  ```sh
  pipenv run deploy_dependencies
  ```
- Deploy raw source files
  ```sh
  pipenv run deploy_raw
  ```
- Try it out
  ```sh
  pipenv run example
  pipenv run example_reset
  ```

# CI
```sh
pipenv sync
pipenv run linter
pipenv run typechecker
```


# Reference
- https://www.cutestrap.com/