# TODO

- Investigate left-half battery showing `0%` on display despite measured cell voltage around `3.9V`.
  - Suspected config gap: explicit battery reporting fetch mode not set.
  - Candidate fix to test: set `CONFIG_ZMK_BATTERY_REPORTING_FETCH_MODE_LITHIUM_VOLTAGE=y` for the left build.
  - Validate by rebuilding/flash and confirming non-zero battery percentage on left display.

- Tune home-row mods (HRM) to reduce accidental modifier activations and perceived latency.
  - Add a custom hold-tap behavior in `config/hillside_view.keymap` (e.g. `hrm`) with:
    - `flavor = "tap-preferred"`
    - `tapping-term-ms = <170>`
    - `quick-tap-ms = <130>`
    - `require-prior-idle-ms = <150>`
  - Replace Base-layer home-row `&mt ...` bindings with `&hrm ...`.
  - Build and test both halves.
  - If accidental mods persist, tune `tapping-term-ms` down and `require-prior-idle-ms` up.
  - Optional advanced follow-up: add opposite-hand hold triggers.

- Fix key-position alignment for right half in `config/hillside_view.keymap`.
  - Base layer row `2,*` currently shifted because extra center bindings push right-half positions.
  - Expected Base right row mapping at `(2,0..5)`: `N M , . / -`.
  - Verify and correct Numbers right row mapping at `(2,0..5)`: `RALT \\ 1 2 3 *`.
  - Keep center keys explicit so the right-half positions do not shift again.
