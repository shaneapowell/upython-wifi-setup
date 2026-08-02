#!/usr/bin/env python3
"""Spawn ble-serial, then hand off to miniterm on /tmp/ttyBLE."""
import os
import subprocess
import sys
import time

PTY_PATH = "/tmp/ttyBLE"

if len(sys.argv) < 2:
    print("Usage: ble-uart-term.py <MAC_ADDRESS>")
    sys.exit(1)

mac = sys.argv[1]

# Clean stale PTY
if os.path.exists(PTY_PATH):
    os.unlink(PTY_PATH)

# Spawn ble-serial in background
subprocess.Popen(
    ["ble-serial", "-d", mac, "-t", "10", "--write-with-response"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

# Wait for PTY
for _ in range(60):
    if os.path.exists(PTY_PATH):
        break
    time.sleep(0.2)
else:
    print(f"Timeout waiting for {PTY_PATH}")
    sys.exit(1)

# Give ble-serial time to actually connect to the device
time.sleep(4)

# Replace ourselves with miniterm (echo on so we see what we type)
os.execvp("python3", ["python3", "-m", "serial.tools.miniterm", "--echo", PTY_PATH, "115200"])
