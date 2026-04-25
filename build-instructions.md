# Build Instructions

This file is the authoritative local build guide for this repository.

## Source Of Truth

- `build.yaml` is the source of truth for build targets, full shield lists, and snippets.
- `config/` is the source of truth for keymaps, overlays, and Kconfig.
- `scripts/build-firmware.ps1` must mirror `build.yaml` for any locally scripted Hillside View builds.
- If `build.yaml` and `scripts/build-firmware.ps1` disagree, fix the script first and do not trust the local build output.

## Current Hillside View Targets

- Left: `board: nice_nano/nrf52840/zmk`, `shield: hillside_view_left nice_view`, `snippet: zmk-usb-logging`
- Right: `board: nice_nano/nrf52840/zmk`, `shield: hillside_view_right nice_view`, `snippet: none`
- Settings reset: `board: nice_nano`, `shield: settings_reset`

## Before Building

1. Confirm the intended target in `build.yaml`.
2. Confirm the local script still matches the target's `board`, full `shield` string, and `snippet`.
3. Confirm any diagnostic config changes are present in `config/` and are intentional.
4. Do not silently drop auxiliary shields such as `nice_view`.

## Hard Stop Rules

Stop and fix the setup before flashing if any of these occur:

1. Build output does not show the full expected shield string from `build.yaml`.
2. Build output snippet differs from `build.yaml`.
3. Local helper script target definitions differ from `build.yaml`.
4. You cannot prove which config files were merged.

## Recommended Local Build

Build both Hillside View halves with the PowerShell helper:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-firmware.ps1 -Target both
```

Build one half only:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-firmware.ps1 -Target left
powershell -ExecutionPolicy Bypass -File .\scripts\build-firmware.ps1 -Target right
```

## What The Helper Script Does

- Uses the local ZMK checkout at `C:\Daten\GIT\zmk`
- Builds from `C:\Daten\GIT\zmk\app`
- Applies `config/` as `-DZMK_CONFIG`
- Adds module directories from `modules/`
- Produces UF2 output in the ZMK build directory
- Produces DFU ZIPs in `scripts/`

## Manual Verification After Every Build

Inspect the build output and verify all of the following:

1. `Shield(s): hillside_view_left nice_view` for the left build
2. `Shield(s): hillside_view_right nice_view` for the right build
3. The expected snippet is listed
4. The expected config files are merged
5. The build completes without errors

For this repo, a valid Hillside left build should show all of:

- `Board: nice_nano/nrf52840/zmk`
- `Shield(s): hillside_view_left nice_view`
- `Snippet(s): zmk-usb-logging`

A valid Hillside right build should show all of:

- `Board: nice_nano/nrf52840/zmk`
- `Shield(s): hillside_view_right nice_view`
- no snippet listed

If any shield, snippet, or merged config is not what you expected, stop and fix the build inputs before flashing.

## Expected Build Artifacts

- Left DFU ZIP: `scripts/hillside_view_left-nice_nano_nrf52840_zmk-zmk-dfu.zip`
- Right DFU ZIP: `scripts/hillside_view_right-nice_nano_nrf52840_zmk-zmk-dfu.zip`
- Left UF2: `C:\Daten\GIT\zmk\app\build\hillside_view_left-nice_nano_nrf52840_zmk\zephyr\zmk.uf2`
- Right UF2: `C:\Daten\GIT\zmk\app\build\hillside_view_right-nice_nano_nrf52840_zmk\zephyr\zmk.uf2`

## Diagnostic Build Changes

For diagnostic builds, keep the change set minimal and explicit.

- Prefer changing one variable at a time.
- Document temporary logging or Bluetooth changes in the commit or working notes.
- Keep `build.yaml` and the local script aligned even for diagnostic builds.
- If a diagnostic build needs a different snippet than normal firmware, record that change explicitly and revert it explicitly.

## Common Failure Mode To Avoid

Do not build Hillside View with only `hillside_view_left` or only `hillside_view_right` when `build.yaml` specifies `hillside_view_left nice_view` or `hillside_view_right nice_view`.

Dropping `nice_view` can produce firmware that appears to have an old or incorrect display configuration even when the keymap files are current.

## Rebuild Requirement After Build-Input Changes

If you change any of the following, a fresh rebuild is required before flashing:

1. `build.yaml`
2. `scripts/build-firmware.ps1`
3. Any `config/*.conf`, keymap, shield overlay, or dtsi used by the target
4. Any snippet selection or snippet config
