# KNOWLEDGE.md

Reference notes for debugging and future sessions.

## Known-good reference builds

### b83clean (config commit b83ace9, ZMK commit 9490391e)

- **BLE pairing with PC**: Works (confirmed on Lenovo ThinkPad with MediaTek MT7921 adapter)
- **Split connectivity**: Works (left + right halves pair and communicate)
- **Display (nice!view)**: Works
- **Keyboard input via USB**: Works
- **Keyboard input via BLE**: Works (keypresses register on PC wirelessly)
- **Bond persistence**: BROKEN (`board: nice_nano` without `/nrf52840/zmk` qualifier results in `CONFIG_SETTINGS_NONE=y` — no NVS, bonds lost on reboot)
- **Build hex files**: `C:\Daten\GIT\zmk-9490\app\build\b83clean-left\zephyr\zmk.hex` and `b83clean-right`
- **DFU zips**: `scripts/b83clean-left-dfu.zip` and `scripts/b83clean-right-dfu.zip`
- **Config worktree**: `C:\Daten\GIT\zmk-config-b83clean\`

### Current build (board: nice_nano/nrf52840/zmk, ZMK commit 9490391e)

- **NVS/flash storage**: Works (`CONFIG_SETTINGS_NVS=y`)
- **Display (nice!view)**: Works
- **Split connectivity**: Works
- **BLE pairing with PC**: Works, bonds persist across power cycles
- **Keyboard input via USB**: Works
- **Keyboard input via BLE**: Works
- **DFU zips**: `scripts/hillside_view_left-nice_nano_nrf52840_zmk-zmk-dfu.zip` and right variant

## Resolved issues — root causes and fixes

### Display not working
- **Root cause**: ZMK workspace (`C:\Daten\GIT\zmk`) was on `v0.3-branch` (commit `acfd8e5e`) instead of `main`. This pulled Zephyr 3.5 / LVGL 8.3 instead of Zephyr 4.1 / LVGL 9.3. ZMK's display code targets LVGL 9 — the API/ABI break between LVGL 8 and 9 caused display failure.
- **Fix**: `git checkout 9490391e` in ZMK workspace, then `west update` to resolve correct dependencies.

### BLE bonds not persisting (and cascade BLE failures)
- **Root cause**: `build.yaml` used `board: nice_nano` instead of `board: nice_nano/nrf52840/zmk`. Without the full board qualifier, the ZMK board variant defconfig was not loaded, resulting in `CONFIG_SETTINGS_NONE=y` — no NVS flash storage. BLE bonds, split bonds, and all settings lived only in RAM and were lost on every reboot.
- **Fix**: Changed `build.yaml` to `board: nice_nano/nrf52840/zmk`. This loads the correct defconfig with `CONFIG_FLASH=y`, `CONFIG_NVS=y`, `CONFIG_SETTINGS_NVS=y`.

### BLE pairing err 4 (BT_SECURITY_ERR_AUTH_REQUIREMENT)
- **Root cause**: A cascade failure from the missing NVS. Without persistent bonds, every reboot lost the pairing. The PC kept reconnecting with saved keys the keyboard no longer had. Repeated pair/delete cycles in Windows poisoned the BLE state, causing Windows to fall back to legacy pairing — which ZMK rejects because it enforces `CONFIG_BT_SMP_SC_PAIR_ONLY=y` (LE Secure Connections only).
- **Fix**: Once NVS was fixed (bonds persist), a clean flash cycle (settings_reset + real firmware on both halves, clean Windows BT state) allowed SC pairing to succeed. Bonds now survive power cycles, breaking the cascade.
- **Note**: The MediaTek MT7921 adapter fully supports SC pairing. The err 4 was not a hardware limitation.

## BLE pairing notes

- ZMK unconditionally enforces `CONFIG_BT_SMP_SC_PAIR_ONLY=y` (LE Secure Connections only) via a Kconfig `select` in `zmk/app/Kconfig:150`. This has been present since ZMK's first commit (June 2020). It cannot be overridden by user config — only by patching ZMK's Kconfig.
- The b83clean build proves the MediaTek MT7921 adapter CAN negotiate SC pairing successfully.
- Repeated pair/delete cycles in Windows can poison the BLE state, causing the PC to fall back to legacy pairing (which ZMK rejects with err 4). Cleaning `HKLM\...\BTHPORT\Parameters\PerDevices` and restarting `bthserv` helps. The real fix is ensuring NVS works so bonds persist and the pair/delete cycle never happens.
- Failed PC pairing attempts can poison the ZMK split peripheral slot (`peripherals[0].conn` stuck non-NULL), causing the right half to disconnect. Power cycle of both halves is required to recover. This is a ZMK firmware bug in `central.c` but is not triggered when pairing works correctly.
- The `board: nice_nano` vs `board: nice_nano/nrf52840/zmk` distinction is critical. Always use the full qualifier to get NVS support.

## Boot and flash procedures

- Flash order: left first, then right
- Boot order: left first, wait 5-10s, then right
- Before pairing with PC: ensure split is connected first, then add device in Windows
- After failed pairing: remove device from Windows BT settings, power-cycle both halves before retrying
- Settings reset procedure: flash `settings_reset` to both halves, let boot for 5s, then flash real firmware to both halves

### COM port assignments

Ports are stable per half but differ between bootloader and normal mode.

| Half  | Bootloader | Normal mode |
|-------|-----------|-------------|
| Left  | COM27     | COM5        |
| Right | COM6      | COM6        |

Bluetooth serial ports (COM25, COM26) are always present and unrelated to USB.

## PC Bluetooth adapter

- Foxconn / Hon Hai MediaTek MT7921 (USB VID 0489, PID E0CD)
- BLE 5.x, supports LE Secure Connections
- PC BT MAC: stored privately in `secrets/bluetooth.md`
