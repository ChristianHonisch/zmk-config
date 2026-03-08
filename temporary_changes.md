# Temporary Changes for Hold-Tap Diagnostics

These changes enable USB serial logging on the left (central) half to capture
hold-tap decision timing data. They should be reverted after the diagnostic
session is complete.

## Purpose

Diagnose accidental home-row mod activations (e.g., typing "ar" produces
"Ctrl+R") by capturing firmware-internal hold-tap decision logs with
microsecond-precision timestamps. The logs are captured by
`scripts/capture-ht-log.py` and analyzed by `scripts/analyze-ht-log.py`.

## Changes Made

### 1. `config/hillside_view_left.conf` — USB logging
- **Change:** Added `CONFIG_ZMK_USB_LOGGING=y` (left-only conf, not shared)
- **Also:** In `config/hillside_view.conf` line 24, the original shared entry
  was commented out and annotated as moved.
- **Effect:** Enables Zephyr debug logging over USB CDC ACM serial on the left
  (central) half only. All ZMK debug messages (not just hold-tap) are output.
  LOG_LEVEL defaults to 4 (DBG).
- **Side effect:** Deep sleep is disabled while USB logging is active (USB stack
  must stay awake).
- **Revert:** Remove `CONFIG_ZMK_USB_LOGGING=y` from `hillside_view_left.conf`
  and remove the comment in `hillside_view.conf`.

### 2. `config/boards/shields/hillside_view/hillside_view_left.overlay` line 28
- **Change:** Commented out `zephyr,console = &snippet_studio_rpc_usb_uart;`
- **Reason:** This line assigns the Studio UART as the Zephyr console, which
  conflicts with USB logging (which needs `zephyr,console` for its own UART).
  Studio does NOT actually need `zephyr,console` — it uses
  `zmk,studio-rpc-uart` (a separate chosen node set by its own snippet).
  This line was technically a bug even before this change.
- **Revert:** Uncomment the line (or better: delete it permanently, see
  bugs_to_fix.md item 3).

### 3. `scripts/build-firmware.ps1` line 162
- **Change:** Snippet changed from `studio-rpc-usb-uart` to `zmk-usb-logging`
- **Effect:** The left-half build uses the ZMK USB logging snippet instead of the
  Studio RPC snippet. This creates a CDC ACM UART for log output instead of
  Studio RPC.
- **Side effect:** ZMK Studio is not available on the left half during diagnostics.
- **Revert:** Change back to `Snippet = "studio-rpc-usb-uart"`

## How to Revert All Changes

1. In `config/hillside_view_left.conf`: remove `CONFIG_ZMK_USB_LOGGING=y` line
   In `config/hillside_view.conf`: remove the comment about "moved to left.conf"
2. In `hillside_view_left.overlay`: uncomment `zephyr,console` line (or delete it)
3. In `build-firmware.ps1`: change snippet back to `studio-rpc-usb-uart`
4. Rebuild both halves: `build-firmware.ps1 -Target both`
5. Flash both halves
6. Delete this file
