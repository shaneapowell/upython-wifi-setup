# AGENTS.md

## Project Overview

**uPython WiFi Setup** — A WiFi setup portal library for MicroPython-based ESP32 boards. Provides a captive portal web UI and an optional BLE UART protocol for provisioning WiFi credentials on resource-constrained devices.

- **Repo:** `shaneapowell/upython-wifi-setup`
- **Target runtime:** MicroPython on ESP32 (tested on SEEED Xiao ESP32-S3 and ESP32-C3)
- **Dependencies:** `microdot`, `utemplate`, `aioble` (BLE only)

## Architecture

The library has two parts: Python source code and web assets, kept separate for easy customization.

### Source (`src/uwifisetup/`)

| File | Purpose |
|------|---------|
| `setup.py` | Captive portal: AP mode, DNS server, microdot web server, template routing |
| `wifi.py` | WiFi credential management (save/load to `creds.json`) and STA connection |
| `blesetup.py` | BLE Nordic UART provisioning (JSON request/response protocol) |
| `log.py` | Colored console logging (debug/info/warn/error/fatal) |
| `util.py` | Utility helpers (`file_exists`) |

### Assets (`src/www/_uwifisetup/`)

HTML template files and static assets served by the captive portal. During compilation, `utemplate_util.py` converts `.html` templates into `.py` files (e.g., `welcome.html` → `welcome_html.py`). These compiled templates are then optionally pre-compiled to `.mpy` for deployment.

### Submodules (`lib/`)

| Path | Purpose |
|------|---------|
| `lib/utemplate` | Template engine (https://github.com/pfalcon/utemplate) |
| `lib/microdot` | HTTP framework (https://github.com/miguelgrinberg/microdot) |

## Project Structure

```
src/uwifisetup/       — Library source code
src/www/              — HTML templates and static assets
dist/                 — Compiled output (.mpy files + assets)
examples/             — Example entry points for testing on device
tools/                — Build, deploy, and validation scripts
lib/                  — Git submodules (utemplate, microdot)
docs/                 — Screenshots and API documentation
package*.json         — MIP package manifests for device installation
```

## Development Workflow

### Prerequisites

- Docker installed
- ESP32 device connected via USB (set `USB_DEVICE` in `.env`, default `/dev/ttyACM0`)

### Setup

```bash
git clone https://github.com/shaneapowell/upython-wifi-setup.git
git submodule init && git submodule update
```

### Key Commands (via Makefile + Docker)

All commands run inside a Docker dev container. The container is started automatically by `make`.

| Command | Description |
|---------|-------------|
| `make build` | Compile templates to `.py`, then source to `.mpy` in `dist/` |
| `make clean` | Clean build artifacts (template `.py` + `dist/*`) |
| `make lint` | Run flake8 on `src/uwifisetup` |
| `make typecheck` | Run mypy on `src/uwifisetup` |
| `make test` | Prompt: run emulator or hardware tests |
| `make etest` | Run unit tests on micropython emulator (src + dist, excludes `test_wifi`) |
| `make htest` | Deploy raw source + deps, run all unit tests on device |
| `make validate` | Clean + rebuild + hash compare (CI check) |
| `make deploy` | Deploy compiled `dist/` to device `/lib` via rshell |
| `make deploy_raw` | Deploy raw source to device `/lib` via rshell |
| `make deploy_deps` | Install dependencies to device via mpremote |
| `make run_example` | Run the WiFi portal example on device |
| `make run_example_ble` | Run the BLE UART example on device |
| `make run_example_reset` | Clear WiFi credentials on device |
| `make mprepl` | Open mpremote REPL on device |
| `make mpshell` | Open rshell session on device |
| `make mprun FILE=example.py` | Run arbitrary file on device |
| `make shell` | Drop into bash inside dev container |
| `make up` | Start persistent dev container |
| `make down` | Stop persistent dev container |

### Development Mode (Live Templates)

For active development on templates, edit `src/uwifisetup/setup.py` and switch from the compiled loader to the source loader:

```python
# Change from:
# DEFAULT_TEMPLATE_LOADER_CLASS = compiled.Loader
# To:
DEFAULT_TEMPLATE_LOADER_CLASS = utemplate.source.Loader
```

Then deploy raw source: `make deploy_raw`

## CI Pipeline

Defined in `.github/workflows/tests.yml` (runs inside Docker container):
1. **lint-and-typecheck** — flake8 + mypy on `src/uwifisetup`
2. **verify-dist** — clean + rebuild + hash compare (ensures dist is in sync)

Run locally: `make lint && make typecheck && make validate`

## Code Conventions

- **Linter:** flake8, max line length 200, ignores E303 and W504 (see `tox.ini`)
- **Type checker:** mypy with `--check-untyped-defs`
- **MicroPython imports:** Use `# type: ignore [import-untyped, import-not-found]` for MicroPython built-in modules (`network`, `machine`, `ubluetooth`, `uasyncio`)
- **Logging:** Use `uwifisetup.log` module with `log.info(__name__, "message")` pattern
- **Async:** All WiFi operations use `uasyncio` (imported as `asyncio` in source)
- **Credentials:** Stored as JSON in `/creds.json` on device filesystem

## Key Functions

### `uwifisetup.setup.setupWifi(...)`
Starts the captive portal. Parameters: `deviceName`, `appName`, `welcomeMessage`, `completeMessage`, `templateFileRoot`, `resetDeviceWhenSetupComplete`, `usePreCompiledTemplates`.

### `uwifisetup.blesetup.setupWifi(...)`
Starts BLE UART provisioning. Parameters: `deviceName`, `deviceInfo`, `advertiseAppearance`, `resetDeviceWhenSetupComplete`.

### `uwifisetup.wifi`
- `hasCredentials()` — check if creds exist
- `connectWifi(deviceName)` — async connect using saved creds
- `saveCredentials(ssid, pwd)` / `loadCredentials()` — credential I/O
- `factoryReset()` — delete creds file

## BLE UART Protocol

JSON-based request/response over Nordic UART service. Messages are chunked at 256 bytes per BLE packet (recommend ≤128 bytes) and reassembled internally up to 1024 bytes. Each message is delimited by `\r` (carriage return). The protocol is pseudo-synchronous — only one request in-flight at a time.

| Request | Description |
|---------|-------------|
| `get_device_info` | Returns device name and info dict |
| `get_available_wifi` | Streams available networks (strongest first), ends with `done` |
| `connect_to_wifi` | Connects to specified SSID/password |
| `complete` | Signals setup is done, optionally resets device |
| `write_file` | Append a base64-encoded data chunk to a file |
| `file_hash` | Return MD5 hex digest of a file |
| `delete_file` | Remove a file |

Response codes: `ok`, `error` (with `msg`), `done`

**`write_file` notes:**
- `data` field is base64-encoded; device decodes to raw bytes before writing
- `truncate` (optional, default `false`): `true` creates/overwrites, `false` appends
- Filenames are root-relative; leading `/` auto-prefixed if missing

## Testing on Device

1. Deploy: `make deploy` (compiled) or `make deploy_raw` (source)
2. Run example: `make run_example`
3. Connect phone to "MyPyDevice" AP, complete WiFi setup in browser
4. Device resets, re-run example to verify connection
5. Reset creds: `make run_example_reset` or `mpremote rm /creds.json`

## Important Notes

- The `dist/` directory contains pre-compiled `.mpy` files and should be committed
- Template `.py` files in `src/www/_uwifisetup/` are generated artifacts (gitignored)
- `.env` contains `RSHELL_PORT` for device serial port — do not commit changes
- Asset files (CSS, images, SVGs) cannot be frozen into firmware; they must live on device filesystem
- When freezing into custom firmware: `.py` files go in `modules/`, assets go in device filesystem
