# RstEye

Desktop break reminder for Ubuntu and macOS.

## Install

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
rsteye
```

Run it from a logged-in graphical desktop session.

## Configuration

Set these environment variables before starting:

```sh
export POPUP_INTERVAL=60  # minutes between reminders
export POPUP_DURATION=60  # seconds for each break
```

The app also reads `.env` from `~/.config/rsteye/` on Ubuntu or
`~/Library/Application Support/RstEye/` on macOS.

## Build

Install the build dependency:

```sh
python -m pip install -e '.[build]'
```

Validate the bundled assets:

```sh
python scripts/validate_resources.py
```

Build the Ubuntu binary:

```sh
python -m PyInstaller --clean --noconfirm --name rsteye --onefile --windowed \
  --paths src \
  --add-data "src/rsteye/resources/med.gif:rsteye/resources" \
  --add-data "src/rsteye/resources/rsteye.png:rsteye/resources" \
  --hidden-import=PIL.ImageTk \
  --additional-hooks-dir=packaging/pyinstaller/hooks app.py
```

Build the macOS app by running the same command with `--onedir`, the macOS
icon, and `--osx-bundle-identifier com.rsteye.rsteye`.
