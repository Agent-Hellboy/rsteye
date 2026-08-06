from __future__ import annotations

import compileall
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    ROOT / "src/rsteye/resources/med.gif",
    ROOT / "src/rsteye/resources/rsteye.png",
    ROOT / "packaging/macos/pkg/RstEyeIcon.icns",
    ROOT / "packaging/linux/rsteye.desktop",
    ROOT / "packaging/linux/debian/control",
    ROOT / "packaging/linux/debian/postinst",
    ROOT / "packaging/linux/debian/postrm",
    ROOT / "packaging/macos/pkg/distribution.xml",
    ROOT / "packaging/macos/pkg/scripts/com.rsteye.rsteye.plist",
    ROOT / "packaging/macos/pkg/scripts/postinstall",
)


def validate_images() -> list[str]:
    errors: list[str] = []
    for path in REQUIRED_FILES[:2]:
        try:
            with Image.open(path) as image:
                image.verify()
        except (OSError, SyntaxError) as exc:
            errors.append(f"{path.relative_to(ROOT)} is not a readable image: {exc}")
    return errors


def validate_metadata() -> list[str]:
    errors: list[str] = []
    plist = ROOT / "packaging/macos/pkg/scripts/com.rsteye.rsteye.plist"
    distribution = ROOT / "packaging/macos/pkg/distribution.xml"

    try:
        ET.parse(plist)
    except ET.ParseError as exc:
        errors.append(f"{plist.relative_to(ROOT)} is invalid XML: {exc}")

    try:
        ET.parse(distribution)
    except ET.ParseError as exc:
        errors.append(f"{distribution.relative_to(ROOT)} is invalid XML: {exc}")

    icon = ROOT / "packaging/macos/pkg/RstEyeIcon.icns"
    try:
        if icon.read_bytes()[:4] != b"icns":
            errors.append(f"{icon.relative_to(ROOT)} does not have an icns header")
    except OSError as exc:
        errors.append(f"{icon.relative_to(ROOT)} cannot be read: {exc}")

    return errors


def main() -> int:
    missing = [path for path in REQUIRED_FILES if not path.is_file()]
    errors = [f"missing required file: {path.relative_to(ROOT)}" for path in missing]
    if not missing:
        errors.extend(validate_images())
        errors.extend(validate_metadata())

    if not compileall.compile_dir(ROOT / "src", quiet=1):
        errors.append("Python compilation failed under src/")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("Resource and packaging validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
