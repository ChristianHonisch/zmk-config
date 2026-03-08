# Bugs and Issues to Fix

Collected from deep repository review on 2026-03-02.
Items are organized by severity. Check off items as they are resolved.

**Status: ALL 33 ITEMS RESOLVED (2026-03-08)**

## BUGS — Actually broken or will cause problems

### 1. ~~`CONFIG_NFCT_PINS_AS_GPIOS=y` silently ignored~~ ✓ RESOLVED
- **Fix applied:** Removed the deprecated line from shield conf.

### 2. ~~`build.yaml` applies Studio snippet to right half~~ ✓ RESOLVED
- **Fix applied:** Removed Studio snippet from right half entry. Added board
  qualifier `nice_nano/nrf52840/zmk` and `artifact-name` fields.

### 3. ~~`zephyr,console` in left overlay references snippet node without guard~~ ✓ RESOLVED
- **Fix applied:** Removed the `zephyr,console` line from left overlay entirely.

### 4. ~~`technical_debt.md` entirely stale~~ ✓ RESOLVED
- **Fix applied:** Deleted the file.

## REDUNDANCIES — Same config set in multiple places

### 5. ~~`CONFIG_BT_CTLR_TX_PWR_PLUS_8=y` duplicated~~ ✓ RESOLVED
- **Fix applied:** Removed duplicate from shield conf.

### 6. ~~`CONFIG_ZMK_DISPLAY=y` tripled~~ ✓ RESOLVED
- **Fix applied:** Removed from per-side shield confs, kept in shared shield conf.

### 7. ~~`CONFIG_ZMK_DISPLAY_WORK_QUEUE_DEDICATED=y` duplicated~~ ✓ RESOLVED
- **Fix applied:** Removed from shield left conf.

### 8. ~~`CONFIG_ZMK_BLE=y` duplicated~~ ✓ RESOLVED
- **Fix applied:** Removed from user left conf.

### 9. ~~`CONFIG_ZMK_SPLIT_BLE=y` redundant~~ ✓ RESOLVED
- **Fix applied:** Kept with comment "explicit for clarity".

### 10. ~~`CONFIG_GPIO=y` / `CONFIG_PINCTRL=y` redundant~~ ✓ RESOLVED
- **Fix applied:** Removed from both shield side confs.

### 11. ~~`CONFIG_ZMK_DISPLAY_BLANK_ON_IDLE=n` duplicated~~ ✓ RESOLVED
- **Fix applied:** Removed from shield left conf.

### 12. ~~LVGL bits-per-pixel / color depth set twice in Kconfig.defconfig~~ ✓ RESOLVED
- **Fix applied:** Removed duplicate from `if ZMK_DISPLAY` block.

### 13. ~~Battery reporting configured asymmetrically~~ ✓ RESOLVED
- **Fix applied:** Moved `CONFIG_ZMK_BATTERY_REPORTING=y` to shared user conf.
  Deleted now-empty per-side user confs.

## CLEANUP — Stale files, dead code, missing .gitignore

### 14. ~~`.gitignore` missing many entries~~ ✓ RESOLVED
- **Fix applied:** Added `scripts/*.zip`, `*.log`, `__pycache__`, `artifacts/`,
  `logs/`, `.opencode/`, `.venv-tools/`.

### 15. ~~`nul` file in repo root~~ ✓ RESOLVED
- **Status:** File does not exist — no action needed.

### 16. ~~19 DFU zip files in `scripts/`~~ ✓ RESOLVED
- **Fix applied:** Covered by `.gitignore` update (#14).

### 17. ~~`config/hillside_view_right.conf` is empty (0 bytes)~~ ✓ RESOLVED
- **Fix applied:** Deleted empty file (and empty left conf).

### 18. ~~`CONFIG_ZMK_RGB_UNDERGLOW=n` is explicit negative~~ ✓ RESOLVED
- **Fix applied:** Removed from user conf along with commented-out encoder lines.

### 19. ~~Commented-out encoder/trackball code in overlays~~ ✓ SKIPPED
- **Status:** Left as-is. Commented-out code in overlays serves as documentation
  for future hardware additions.

### 20. ~~Commented-out RGB/encoder config in shield conf~~ ✓ RESOLVED
- **Fix applied:** Removed commented-out config blocks from shield conf.

## IMPROVEMENTS — Not wrong, but could be better

### 21. ~~Keymap uses magic numbers for layers~~ ✓ RESOLVED
- **Status:** Already done — layer defines exist in keymap.

### 22. ~~Layer name "Symbols" is misleading~~ ✓ RESOLVED
- **Status:** Already renamed to `FKeys`.

### 23. ~~`west.yml` module pinned to mutable branch name~~ ✓ RESOLVED
- **Fix applied:** Pinned `prospector-zmk-module` to commit
  `f117cd8d65da2c6c46f80d5293aac78362ae35a8` and `zmk-locales` to commit
  `be0427eaa80c7bb9a3d74ab11a78d53b98f5c5aa`.

### 24. ~~`README.md` references layers 4-5 that don't exist~~ ✓ RESOLVED
- **Fix applied:** Removed stale layer images and Corne/Charybdis sections.

### 25. ~~Sensors node references disabled encoders~~ ✓ RESOLVED
- **Fix applied:** Added comment to sensors node in dtsi.

### 26. ~~`zmk,underglow = &led_strip` chosen with RGB disabled~~ ✓ RESOLVED
- **Fix applied:** Added comment to underglow chosen in dtsi.

### 27. ~~Makefile upload assumes Linux tools~~ ✓ RESOLVED
- **Fix applied:** Documented in updated AGENTS.md.

### 28. ~~`build.yaml` missing `artifact-name` for cleaner CI output~~ ✓ RESOLVED
- **Fix applied:** Added `artifact-name` fields to build.yaml.

## DOCUMENTATION — Inaccuracies or gaps

### 29. ~~AGENTS.md references nonexistent Cygnus keyboard~~ ✓ RESOLVED
- **Fix applied:** Removed all Cygnus references from AGENTS.md.

### 30. ~~AGENTS.md doesn't document PS1 build workflow~~ ✓ RESOLVED
- **Fix applied:** Added Windows build/flash workflow to AGENTS.md.

### 31. ~~AGENTS.md upload examples use short board name~~ ✓ RESOLVED
- **Fix applied:** Updated to full qualifier `nice_nano/nrf52840/zmk`.

### 32. ~~`README.md` references Corne and Charybdis from upstream fork~~ ✓ RESOLVED
- **Fix applied:** Removed from README.md.

### 33. ~~`CONFIG_ZMK_KEYBOARD_NAME` override creates dead defconfig default~~ ✓ RESOLVED
- **Fix applied:** Added comment to Kconfig.defconfig explaining the override.
