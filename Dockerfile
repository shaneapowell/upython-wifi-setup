FROM python:3.11-slim AS dev

RUN apt-get update && apt-get install -y --no-install-recommends \
    expect \
    gcc \
    git \
    make \
    micropython \
    bluez \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
    mpy-cross \
    flake8 \
    mypy \
    mpremote \
    rshell \
    pydoc-markdown \
    micropython-esp32-stubs \
    tox \
    ble-serial \
    pyserial

WORKDIR /work

CMD [bash]
