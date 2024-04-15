# uPython Wifi Setup

# Information
Inspired by https://github.com/george-hawkins/micropython-wifi-setup

# Goals
- Reliable
- Low Memory Overhead
- ASYNC processing
- Very simple web-browser requirements.  Minimal Javascript.
- Easy to integrate into your existing projects
- Easy to build your project upon

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

# How to use this library


# How to incorporate what this library provides into your project
- include udot web server
- included cutestrap css
- included custom css and js

# Reference
- https://www.cutestrap.com/