# RstEye

Desktop reminder app that opens a full-screen breathing break animation on a timer.

## Layout

```text
.
├── app.py
├── pyproject.toml
├── requirements.txt
├── src/
│   └── rsteye/
│       ├── __main__.py
│       ├── app.py
│       └── resources/
│           ├── med.gif
│           └── rsteye.png
└── packaging/
    ├── linux/debian/
    ├── macos/pkg/
    ├── pyinstaller/hooks/
    └── windows/
```

## What it does

- Shows a reminder popup at a fixed interval.
- Opens an animated GIF for a configurable duration.
- Uses Tkinter, Pillow, and `python-dotenv`.

## Configuration

Set these environment variables before launching the app:

- `POPUP_INTERVAL`: minutes between break prompts, default `60`
- `POPUP_DURATION`: seconds the break animation stays visible, default `60`

Example:

```sh
export POPUP_INTERVAL=120
export POPUP_DURATION=30
```

## Run locally

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

## Build

### Linux

```sh
pyinstaller --name RstEyeApp --windowed --onefile --paths src \
  --add-data "src/rsteye/resources/med.gif:rsteye/resources" \
  --add-data "src/rsteye/resources/rsteye.png:rsteye/resources" \
  --hidden-import=PIL.ImageTk \
  --additional-hooks-dir=packaging/pyinstaller/hooks \
  app.py
```

### macOS

```sh
pyinstaller --name RstEyeApp --windowed --onefile --paths src \
  --add-data "src/rsteye/resources/med.gif:rsteye/resources" \
  --add-data "src/rsteye/resources/rsteye.png:rsteye/resources" \
  --icon=packaging/macos/pkg/RstEyeIcon.icns \
  --hidden-import=PIL.ImageTk \
  --additional-hooks-dir=packaging/pyinstaller/hooks \
  app.py
```

### Windows

```powershell
pyinstaller --name RstEyeApp --windowed --onefile --paths src `
  --add-data "src\rsteye\resources\med.gif;rsteye/resources" `
  --add-data "src\rsteye\resources\rsteye.png;rsteye/resources" `
  --icon=packaging\windows\rsteye.ico `
  --hidden-import=PIL.ImageTk `
  --additional-hooks-dir=packaging\pyinstaller\hooks `
  app.py
```

## Packaging

- `packaging/linux/debian/`: Debian service and control files
- `packaging/macos/pkg/`: macOS installer scripts and resources
- `packaging/windows/setup.iss`: Inno Setup script

## Notes

- The app currently targets desktop environments that support Tkinter windows.
- Packaging outputs are still platform-specific, so macOS, Linux, and Windows builds must be produced on their respective platforms or in matching VMs/containers.
- For Debian installs, check service logs with `journalctl -u rsteye.service -b`.
