FROM ubuntu:24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        python3 \
        python3-pip \
        python3-tk \
        python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY . .

RUN python -m pip install --no-cache-dir '.[build]' \
    && python scripts/validate_resources.py \
    && python -m PyInstaller --clean --noconfirm --name rsteye --onefile \
        --windowed --paths src \
        --add-data "src/rsteye/resources/med.gif:rsteye/resources" \
        --add-data "src/rsteye/resources/rsteye.png:rsteye/resources" \
        --hidden-import=PIL.ImageTk \
        --additional-hooks-dir=packaging/pyinstaller/hooks app.py
