# Script Info

This file documents the runnable scripts in `scripts/`.

Generated artifacts in that directory such as `.zip` packages and `.log` files are not scripts and are intentionally excluded from this list.

## Priority Scripts

### `scripts/flash-firmware.ps1`

- Purpose: Flash the current left and right Hillside View DFU packages over serial bootloader.
- When to use it: Normal firmware flashing after a successful build.
- Parameters:
  - `-LeftComPort` default `COM27`
  - `-RightComPort` default `COM6`
  - `-BaudRate` default `115200`
  - `-Touch` default `1200`
  - `-NoTouch` switch to disable 1200-baud touch reset
- Packages flashed:
  - `scripts/hillside_view_left-nice_nano_nrf52840_zmk-zmk-dfu.zip`
  - `scripts/hillside_view_right-nice_nano_nrf52840_zmk-zmk-dfu.zip`
- Example:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\flash-firmware.ps1 -NoTouch
```

- Notes:
  - Uses `.venv-tools\Scripts\adafruit-nrfutil.exe`.
  - `-NoTouch` is often the more reliable option on this machine.

### `scripts/build-firmware.ps1`

- Purpose: Build left and/or right Hillside View firmware and generate DFU zip packages.
- When to use it: Main local build entrypoint before flashing.
- Parameters:
  - `-ZmkRoot` default `C:\Daten\GIT\zmk`
  - `-ConfigRepo` default repo root
  - `-ToolchainPython` default `C:\ncs\toolchains\fd21892d0f\opt\bin\python.exe`
  - `-Target` one of `both`, `left`, `right`; default `both`
  - `-NoDfuZip` switch to skip DFU package generation
- Outputs:
  - `scripts/hillside_view_left-nice_nano_nrf52840_zmk-zmk-dfu.zip`
  - `scripts/hillside_view_right-nice_nano_nrf52840_zmk-zmk-dfu.zip`
- Example:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-firmware.ps1 -Target both
```

- Notes:
  - Builds from `${ZMK_ROOT}\app` using `west build`.
  - Adds all directories from `modules/` as `ZMK_EXTRA_MODULES`.
  - Current target snippets are left=`zmk-usb-logging`, right=`none`.
  - Hard-fails if `ZEPHYR_*` variables point at an NCS Zephyr tree.

### `scripts/render_keymaps.py`

- Purpose: Render the active Hillside keymap to keymap-drawer YAML and SVG artifacts.
- When to use it: After keymap changes, especially layer/combo/legend changes.
- Parameters: none.
- Outputs:
  - `artifacts/keymap-drawer/hillside_view.yaml`
  - `artifacts/keymap-drawer/hillside_view.svg`
  - `artifacts/keymap-drawer/hillside_view_debug_rc.yaml`
  - `artifacts/keymap-drawer/hillside_view_debug_rc.svg`
- Example:

```powershell
python .\scripts\render_keymaps.py
```

- Notes:
  - Requires `keymap-drawer` CLI in `PATH`.
  - Calls `scripts/de_keymap_translate.py` to rewrite legends for German layout and emoji glyphs.

## Supporting Scripts

### `scripts/flash-bt-reset.ps1`

- Purpose: Flash the `settings_reset` image to both halves to clear persistent settings and bonds.
- Parameters:
  - `-LeftComPort` default `COM27`
  - `-RightComPort` default `COM6`
  - `-BaudRate` default `115200`
  - `-Touch` default `1200`
  - `-NoTouch` switch
- Package flashed:
  - `scripts/settings_reset-nice_nano-zmk-dfu.zip`
- Example:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\flash-bt-reset.ps1 -NoTouch
```

### `scripts/setup-build-env.ps1`

- Purpose: Prepare the local build environment, initialize/update west, and sync external modules from `config/west.yml`.
- Parameters:
  - `-ZmkRoot` default `C:\Daten\GIT\zmk`
  - `-ConfigRepo` default repo root
  - `-ToolchainPython` default `C:\ncs\toolchains\fd21892d0f\opt\bin\python.exe`
  - `-SkipWestUpdate` switch
- Example:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-build-env.ps1
```

### `scripts/de_keymap_translate.py`

- Purpose: Post-process keymap-drawer YAML so legends reflect DE layout output and Unicode emoji glyphs.
- When to use it: Normally not called directly; used by `scripts/render_keymaps.py`.
- Parameters: none as a documented standalone CLI.

### `scripts/capture-synchronous-session.ps1`

- Purpose: Capture both halves' serial logs and a Bluetooth ETW trace in one synchronized session.
- Parameters:
  - `-LeftComPort` default `COM5`
  - `-RightComPort` default `COM3`
  - `-BaudRate` default `115200`
  - `-OutputDir` default `.\logs`
  - `-ProfilePath` default `.\BluetoothStack.wprp`
- Example:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\capture-synchronous-session.ps1
```

- Notes:
  - Self-elevates to admin for ETW capture.
  - Depends on `wpr.exe`.

### `scripts/capture-bluetooth-trace.ps1`

- Purpose: Capture a Bluetooth ETW trace only.
- Parameters:
  - `-ProfilePath` default `.\BluetoothStack.wprp`
  - `-OutputPath` default `.\BthTrace.etl`
- Example:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\capture-bluetooth-trace.ps1
```

### `scripts/capture-ht-log-both.py`

- Purpose: Capture USB serial logs from both halves into one timestamped log file.
- Parameters:
  - `--baud` or `-b` default `115200`
  - `--output-dir` or `-o` default `logs`
  - `--output-file` explicit output path
  - `--stop-file` exit when that file appears
  - `--left` or `-l` default `COM5`
  - `--right` or `-r` default `COM3`
- Example:

```powershell
python .\scripts\capture-ht-log-both.py --left COM5 --right COM3
```

### `scripts/capture-ht-log.py`

- Purpose: Capture one USB serial log stream and preview hold-tap-related lines live.
- Parameters:
  - `--port` or `-p` optional auto-detected COM port
  - `--baud` or `-b` default `115200`
  - `--output-dir` or `-o` default `logs`
- Example:

```powershell
python .\scripts\capture-ht-log.py --port COM5
```

### `scripts/analyze-ht-log.py`

- Purpose: Parse a hold-tap log and generate timing visualizations.
- Parameters:
  - positional log file path
  - `--save` output image path
  - `--start` start time window
  - `--end` end time window
- Example:

```powershell
python .\scripts\analyze-ht-log.py .\logs\ht-log-20260421-220512.log --save timeline.png
```

### `scripts/capture-serial.ps1`

- Purpose: Simple one-port serial capture for a fixed duration.
- Parameters:
  - `-Port` default `COM5`
  - `-BaudRate` default `115200`
  - `-DurationSeconds` default `45`

### `scripts/capture-serial2.ps1`

- Purpose: One-port serial capture with retries and log file output.
- Parameters:
  - `-Port` default `COM5`
  - `-DurationSeconds` default `45`
- Output:
  - `scripts/serial-capture.log`

### `scripts/plot.py`

- Purpose: Ad hoc matplotlib visualization of Hillside geometry coordinates.
- Parameters: none.
- Notes:
  - Development utility, not part of the normal build/flash workflow.

## Common Workflows

### Build Firmware

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-firmware.ps1 -Target both
```

### Flash Firmware

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\flash-firmware.ps1 -NoTouch
```

### Render Keymap

```powershell
python .\scripts\render_keymaps.py
```
