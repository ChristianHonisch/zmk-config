#!/usr/bin/env python3
"""Render keymap-drawer artifacts for the active Hillside keymap.

Outputs:
- hillside_view.yaml: parsed keymap-drawer YAML from ZMK keymap
- hillside_view.svg: all-layer render using local DTS physical layout
- hillside_view_debug_rc.svg: debug render showing RC position labels
"""

from __future__ import annotations

import shutil
import subprocess
import re
from pathlib import Path

from de_keymap_translate import translate_keymap_yaml_file_de


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "artifacts" / "keymap-drawer"
KEYMAP_FILE = ROOT / "config" / "hillside_view.keymap"
SHIELD_DTS = ROOT / "config" / "boards" / "shields" / "hillside_view" / "hillside_view.dtsi"
LAYOUT_DTS = ROOT / "config" / "boards" / "shields" / "hillside_view" / "layouts.dtsi"
LAYOUT_NAME = "hsv_6col_layout"
YAML_OUT = OUT_DIR / "hillside_view.yaml"
SVG_OUT = OUT_DIR / "hillside_view.svg"
DEBUG_YAML_OUT = OUT_DIR / "hillside_view_debug_rc.yaml"
DEBUG_SVG_OUT = OUT_DIR / "hillside_view_debug_rc.svg"


def run(cmd: list[str]) -> None:
    print(">", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True)


def parse_rc_positions(dtsi_path: Path) -> list[str]:
    text = dtsi_path.read_text(encoding="utf-8")
    default_transform_match = re.search(
        r"default_transform:.*?map\s*=\s*<(.*?)>;\s*\n\s*\};",
        text,
        flags=re.DOTALL,
    )
    transform_block = default_transform_match.group(1) if default_transform_match else text
    matches = re.findall(r"RC\((\d+),(\d+)\)", transform_block)
    return [f"r{row}c{col}" for row, col in matches]


def write_debug_yaml(path: Path, layout_dts: Path, layout_name: str, labels: list[str]) -> None:
    quoted_labels = ", ".join(f'"{label}"' for label in labels)
    layout_path = layout_dts.as_posix()
    content = (
        f"layout: {{dts_layout: \"{layout_path}\", layout_name: {layout_name}}}\n"
        f"layers:\n"
        f"  RC:\n"
        f"    - [{quoted_labels}]\n"
    )
    path.write_text(content, encoding="utf-8")


def main() -> None:
    if shutil.which("keymap") is None:
        raise SystemExit(
            "keymap-drawer CLI not found. Install with: pipx install keymap-drawer"
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    run([
        "keymap",
        "parse",
        "-z",
        str(KEYMAP_FILE),
        "-c",
        "12",
        "-o",
        str(YAML_OUT),
    ])

    translate_keymap_yaml_file_de(YAML_OUT)

    run([
        "keymap",
        "draw",
        str(YAML_OUT),
        "-d",
        str(LAYOUT_DTS),
        "-l",
        LAYOUT_NAME,
        "-o",
        str(SVG_OUT),
    ])

    rc_labels = parse_rc_positions(SHIELD_DTS)
    if not rc_labels:
        raise SystemExit(f"No RC() positions found in {SHIELD_DTS}")
    write_debug_yaml(DEBUG_YAML_OUT, LAYOUT_DTS, LAYOUT_NAME, rc_labels)

    run([
        "keymap",
        "draw",
        str(DEBUG_YAML_OUT),
        "-o",
        str(DEBUG_SVG_OUT),
    ])

    print(f"YAML: {YAML_OUT}")
    print(f"SVG : {SVG_OUT}")
    print(f"RC YAML: {DEBUG_YAML_OUT}")
    print(f"RC SVG : {DEBUG_SVG_OUT}")


if __name__ == "__main__":
    main()
