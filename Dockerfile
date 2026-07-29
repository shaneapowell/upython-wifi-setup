FROM python:3.11-slim AS dev

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    make \
    micropython \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
    mpy-cross \
    flake8 \
    mypy \
    mpremote \
    rshell \
    pydoc-markdown \
    micropython-esp32-stubs \
    tox

WORKDIR /work

CMD [bash]
