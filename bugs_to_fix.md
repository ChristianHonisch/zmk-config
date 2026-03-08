# Bugs and Issues to Fix

Collected from deep repository review on 2026-03-02.
Items are organized by severity. Check off items as they are resolved.

## BUGS — Actually broken or will cause problems

### 1. `CONFIG_NFCT_PINS_AS_GPIOS=y` silently ignored
- **File:** `config/boards/shields/hillside_view/hillside_view.conf` line 21
- **Problem:** Deprecated in Zephyr 4.1, does nothing. The DTS fix
  (`&uicr { nfct-pins-as-gpios; }` in `hillside_view.dtsi`) is already in place.
  This line is misleading.
- **Fix:** Remove the line.

### 2. `build.yaml` applies Studio snippet to right half
- **File:** `build.yaml`
- **Problem:** `snippet: studio-rpc-usb-uart` is set for both halves, but the
  `build-firmware.ps1` only applies it to the left (central). CI and local builds
  produce different right-half firmware. Only the central needs Studio.
- **Fix:** Remove `snippet: studio-rpc-usb-uart` from the right-half entry in
  `build.yaml`.

### 3. `zephyr,console` in left overlay references snippet node without guard
- **File:** `config/boards/shields/hillside_view/hillside_view_left.overlay` line 28
- **Problem:** `zephyr,console = &snippet_studio_rpc_usb_uart;` references a node
  that only exists when the `studio-rpc-usb-uart` snippet is applied. If the left
  half is ever built without the snippet, DTS compilation fails. Furthermore,
  Studio does NOT need `zephyr,console` — it uses `zmk,studio-rpc-uart` (set by
  its own snippet). This line is both fragile and unnecessary.
- **Fix:** Remove the `zephyr,console` line entirely.

### 4. `technical_debt.md` entirely stale
- **File:** `technical_debt.md`
- **Problem:** Every item has been resolved. Still describes the sleep bug with a
  wrong hypothesis. Contradicts `docs/bug-deep-sleep-wake.md`.
- **Fix:** Delete the file.

## REDUNDANCIES — Same config set in multiple places

### 5. `CONFIG_BT_CTLR_TX_PWR_PLUS_8=y` duplicated
- **Files:** `config/hillside_view.conf` line 10 AND
  `config/boards/shields/hillside_view/hillside_view.conf` line 2
- **Fix:** Keep in user-level conf only, remove from shield conf.

### 6. `CONFIG_ZMK_DISPLAY=y` tripled
- **Files:** `config/boards/shields/hillside_view/hillside_view.conf` line 5 AND
  `config/boards/shields/hillside_view/hillside_view_left.conf` line 1 AND
  `config/boards/shields/hillside_view/hillside_view_right.conf` line 1
- **Fix:** Keep in shared shield conf only, remove from per-side confs.

### 7. `CONFIG_ZMK_DISPLAY_WORK_QUEUE_DEDICATED=y` duplicated
- **Files:** `config/hillside_view.conf` line 8 AND
  `config/boards/shields/hillside_view/hillside_view_left.conf` line 3
- **Fix:** Keep in user-level conf only, remove from shield left conf.

### 8. `CONFIG_ZMK_BLE=y` duplicated
- **Files:** `config/hillside_view.conf` line 21 AND
  `config/hillside_view_left.conf` line 1
- **Fix:** Keep in user-level conf only, remove from left user conf.

### 9. `CONFIG_ZMK_SPLIT_BLE=y` redundant
- **File:** `config/hillside_view.conf` line 22
- **Problem:** Implied by `ZMK_SPLIT=y` + `ZMK_BLE=y`.
- **Fix:** Remove, or keep with a comment explaining it is explicit for clarity.

### 10. `CONFIG_GPIO=y` / `CONFIG_PINCTRL=y` redundant
- **Files:** `config/boards/shields/hillside_view/hillside_view_left.conf` lines 4-5
  AND `config/boards/shields/hillside_view/hillside_view_right.conf` lines 3-4
- **Problem:** Always enabled on nRF52840 ZMK builds by subsystem dependencies.
- **Fix:** Remove from both.

### 11. `CONFIG_ZMK_DISPLAY_BLANK_ON_IDLE=n` duplicated
- **Files:** `config/boards/shields/hillside_view/hillside_view_left.conf` line 2
  AND `Kconfig.defconfig` line 38-39
- **Fix:** Remove from shield left conf (defconfig already handles it).

### 12. LVGL bits-per-pixel / color depth set twice in Kconfig.defconfig
- **File:** `config/boards/shields/hillside_view/Kconfig.defconfig`
- **Problem:** Lines 50-55 (under `if ZMK_DISPLAY`) and lines 67-73 (under
  `if LVGL`) both set `LV_Z_BITS_PER_PIXEL=1` and color depth.
- **Fix:** Keep only the `if LVGL` block.

### 13. Battery reporting configured asymmetrically
- **Files:** `config/hillside_view_left.conf` line 2 (user-level, left) AND
  `config/boards/shields/hillside_view/hillside_view_right.conf` line 2 (shield-level, right)
- **Fix:** Move to shared conf (user-level `hillside_view.conf` or shared shield conf).

## CLEANUP — Stale files, dead code, missing .gitignore

### 14. `.gitignore` missing many entries
- **File:** `.gitignore` (only 3 lines)
- **Fix:** Add patterns for: `artifacts/`, `scripts/*.zip`, `scripts/__pycache__/`,
  `scripts/*.log`, `.opencode/`, `.venv-tools/`, `nul`, `zephyr/`, `logs/`

### 15. `nul` file in repo root
- **Problem:** Windows artifact from `> NUL` redirection.
- **Fix:** Delete and add to `.gitignore`.

### 16. 19 DFU zip files in `scripts/`
- **Fix:** Add `scripts/*.zip` to `.gitignore`.

### 17. `config/hillside_view_right.conf` is empty (0 bytes)
- **Fix:** Delete, or add a comment placeholder.

### 18. `CONFIG_ZMK_RGB_UNDERGLOW=n` is explicit negative
- **File:** `config/hillside_view.conf` line 6
- **Problem:** RGB underglow is off by default.
- **Fix:** Remove or keep with comment.

### 19. Commented-out encoder/trackball code in overlays
- **Files:** Both left and right overlays
- **Fix:** Keep but add brief comment explaining intent.

### 20. Commented-out RGB/encoder config in shield conf
- **File:** `config/boards/shields/hillside_view/hillside_view.conf` lines 8-18
- **Fix:** Remove or consolidate to a single comment.

## IMPROVEMENTS — Not wrong, but could be better

### 21. Keymap uses magic numbers for layers
- **File:** `config/hillside_view.keymap`
- **Fix:** Add `#define DEF 0`, `#define NUM 1`, `#define NAV 2`, `#define SYM 3`.

### 22. Layer name "Symbols" is misleading
- **File:** `config/hillside_view.keymap`
- **Problem:** Layer 3 contains F-keys, not symbols.
- **Fix:** Rename to `Func` or `FN`.

### 23. `west.yml` module pinned to mutable branch name
- **File:** `config/west.yml`
- **Problem:** `prospector-zmk-module` uses
  `revision: fix/new-status-screan-zmk-refactor` (a branch, with a typo).
- **Fix:** Pin to a commit hash for reproducibility.

### 24. `README.md` references layers 4-5 that don't exist
- **Fix:** Update or remove stale layer image references.

### 25. Sensors node references disabled encoders
- **File:** `config/boards/shields/hillside_view/hillside_view.dtsi`
- **Fix:** Add comment or disable the sensors node.

### 26. `zmk,underglow = &led_strip` chosen with RGB disabled
- **File:** `config/boards/shields/hillside_view/hillside_view.dtsi`
- **Fix:** Remove or add comment noting it is available but disabled via Kconfig.

### 27. Makefile upload assumes Linux tools
- **Fix:** Document this limitation in AGENTS.md.

### 28. `build.yaml` missing `artifact-name` for cleaner CI output
- **Fix:** Add explicit `artifact-name` fields.

## DOCUMENTATION — Inaccuracies or gaps

### 29. AGENTS.md references nonexistent Cygnus keyboard
- **Fix:** Remove all Cygnus references or note as planned/future.

### 30. AGENTS.md doesn't document PS1 build workflow
- **Fix:** Add Windows build section.

### 31. AGENTS.md upload examples use short board name
- **Fix:** Update to full qualifier.

### 32. `README.md` references Corne and Charybdis from upstream fork
- **Fix:** Remove or mark as historical.

### 33. `CONFIG_ZMK_KEYBOARD_NAME` override creates dead defconfig default
- **Files:** `config/hillside_view.conf` sets `"CBH HSV"`,
  `Kconfig.defconfig` defaults to `"Hillside View"`.
- **Fix:** Update defconfig default to match, or add comment explaining override.
