# Technical Debt / Experimental Changes

## Uncommitted experimental changes in zmk-config

These changes were made during deep-sleep wake debugging and should be
reverted or finalized once the root cause is resolved.

### config/hillside_view.conf
- `CONFIG_ZMK_IDLE_SLEEP_TIMEOUT=30000` — reduced from 900000 (15 min) to 30s for faster sleep/wake testing. **Revert to 900000 when done.**
- `CONFIG_ZMK_USB_LOGGING=y` commented out — disabled to test if USB logging device count affects wake. Did NOT fix wake. **Decide: keep disabled for production, or re-enable for debugging.**
- `CONFIG_ZMK_STUDIO=y` + stack size commented out — disabled to test if Studio RPC transport affects wake. Did NOT fix wake. **Re-enable when done — Studio is a useful feature.**

### config/boards/shields/hillside_view/hillside_view_left.overlay
### config/boards/shields/hillside_view/hillside_view_right.overlay
- `zephyr,console = &snippet_studio_rpc_usb_uart;` commented out — required when Studio snippet is removed from build, otherwise DTS references a nonexistent node. **Uncomment when Studio is re-enabled.**

### scripts/build-firmware.ps1
- Studio snippet (`-S studio-rpc-usb-uart`) removed from build targets (Snippet parameter set to empty string, made optional). **Restore snippet when Studio is re-enabled.**

## Known issues not yet fixed

### CONFIG_NFCT_PINS_AS_GPIOS silently ignored
- `hillside_view.conf` (shield) has `CONFIG_NFCT_PINS_AS_GPIOS=y` but it is **deprecated** in Zephyr 4.1 and does not appear in the final `.config`.
- P0.09 and P0.10 are used as kscan columns on both halves.
- **Fix**: Add `&uicr { nfct-pins-as-gpios; };` to DTS (either dtsi or both overlays).

### Deep sleep wake failure on central (left) half
- Issue #3207 on zmk GitHub — known regression from Zephyr 4.1 upgrade.
- Right (peripheral) half wakes on keypress. Left (central) does NOT.
- Both halves use identical sleep code path (activity.c).
- Tested and ruled out: disabling USB logging, disabling Studio, irq_lock before suspend, SUSPEND->RESUME cycle on wakeup devices.
- Current hypothesis: nRF USBD controller PM suspend callback (central-only due to CONFIG_ZMK_USB=y) leaves hardware state that interferes with GPIO SENSE wake detection.
- Next test: build left half with CONFIG_ZMK_USB=n.
