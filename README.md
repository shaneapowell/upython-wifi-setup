# Work In Progress
**This library is still under active development.**


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

# Dependencies
The following 2 libraries are required dependencies.  Recommended you drop these into your `/lib` directory on your device
- [utemplate](https://github.com/pfalcon/utemplate)
  - copy the directory `utemplate` in the repo to `/lib/utemplate` on your device
- [microdot](https://github.com/miguelgrinberg/microdot)
  - copy the directory `src/microdot` to `/lib/microdot` on your device
  - note, Not all microdot files are needed, you can skip the ones you don't want to use yourself. the only required files for this library are:
    - `__init__.py`
    - `microdot.py`
    - `utemplate.py`

# The Library Contents
Made up of 2 main parts. The .py source files, and the assets.
They are kept separate to simplify customizing this library.

## `uwifisetup` - The source
This is the library python files.  These files need to be in the `/lib` or the `/` root of your device.  Or, pre-frozen in the `modules` directory of a custom micropython firmware.

## `www` - The Assets
This is the assets directory.  Contains the `.html` template files, and a handfull of image and css assets.
These files by default are loaded from `/lib/uwifisetup/www` from your device. That is the default install location using the mip install method below.
If you wish to move these to a different install location on yoru deivce, you need only specify a different `templateFileRoot` parameter to `setup.setupWifi(...)`


# Easiest Install
This will put all the source and asset files into the device `/lib` directory.  You'll have to manually move the `www` content if you wish to customize things.
```
mpremote mip install "github:shaneapowell/upython-wifi-setup/package-deps.json"
mpremote mip install "github:shaneapowell/upython-wifi-setup/package.json"
```


# Easy Install
- Clone this repo
  ```
  git clone https://github.com/shaneapowell/upython-wifi-setup.git
  ```
- install `pipenv`.
  ```
  pip3 install pipenv
  ```
- Plug in your micropython esp32 device usb to your computer.  The `Pipfile` has `/dev/ttyACM0` hard-coded as your upy device.
- Sync the pipenv venv packages. This is only needed once, or with any new updates to the `Pipfile`.
  ```
  pipenv sync
  ```
- Install the [microdot](https://github.com/miguelgrinberg/microdot) and [utemplate](https://github.com/pfalcon/utemplate/) package dependencies into `/lib` on the device
  ```sh
  pipenv run deploy_dependencies
  ```
- Optional build the pre-compiled parts. Optional because the `dist` folder should already have the most recent-pre-compiled.
  Note: YOu'll see some like `ModulenotFoundError: No Module named `_uwifisetup/complete_html`. You can safely ignore those.
  ```sh
  pipenv run build
  ```
- Deploy the code and assets into the `/lib` directory.
  ```sh
  pipenv run deploy /dev/ttyACM0
  ```

- Run the example
  ```
  pipenv run example
  ```
- Connect your phone to the wifi access point named `MyPyDevice`
- After the setup is complete, the device should reset itself.
- Re-Run the above example, and the command should finish with a message
  ```
  Connected tdo wifi Success
  ```
- Re-Run the example now, to see the wifi connect using your new creds
  ```sh
  pipenv run example
  ```
- Re-Set your creds to try all over again
  ```sh
  pipenv run example_reset
  ```

# Manual Install
Because you're the type of person who needs to do things manually.  You can inspect the `Pipfile` for commands to reference.
- Manually Install the `microdot` and `utemplate` dependencies.
- Manually copy over the `dist/uwifisetup` files to `/lib/uwifisetup`.
- Manually copy over the `dist/www` files to `/lib/uwifisetup/www`


# Freeze into a custom firmware
TBD

# Credentials
The access point name, and wifi password are stored in a plain text json file `creds.json` in the root of the data parition.

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
- include udot web server
- included cutestrap css
- included custom css and js

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
  pipenv run deploy_raw /dev/ttyACM0
  ```
- Try it out
  ```sh
  pipenv run example
  pipenv run example_reset
  ```

# CI
- pipenv sync
- pipenv run linter
- pipenv run typechecker


# Reference
- https://www.cutestrap.com/