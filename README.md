# uPython Wifi Setup

# Information
Inspired by https://github.com/george-hawkins/micropython-wifi-setup

# Goals
- Reliable
- Low Memory Overhead
- ASYNC processing
- Very simple web-browser requirements.  Minimal Javascript.
- No separate web-app build step.
- Easy to integrate into your existing projects
- Easy to build your project upon

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

# Easy Install
- Clone this repo
- Plug in your micropython esp32 device usb to your computer
- Sync the pipenv venv packages. This is only needed once, or with any new updates to the `Pipfile`.
  ```
  run `pipenv sync
  ```
- Deploy the code and assets
  ```
  pipenv run deploy_library
  pipenv run deploy_assets
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

# Manual Install
- copy src/uwifisetup to your micropython controller
    ```
    cd src
    mpremote cp -r uwifisetup/ :
    ```
- copy assets/_uwifisetup to your micropython controller
    ```
    cd assets
    mpremote cp -r _uwifisetup/ :
    ```
- `import uwifisetup`

# mip Install
```
mpremote mip install github:shaneapowell/upythn-wifi-setup
```

# How to use this library


# How to incorporate what this library provides into your project
- include udot web server
- included cutestrap css
- included custom css and js

# Development

# CI
- pipenv sync
- pipenv run linter
- pipenv run typechecker


# Reference
- https://www.cutestrap.com/