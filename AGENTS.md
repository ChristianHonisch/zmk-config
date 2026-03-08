# AGENTS.md
Guidance for coding agents operating in this repository.
This repository is a ZMK firmware config workspace for split keyboards.
Primary keyboard is Hillside View.

## Scope and source of truth
- `build.yaml` is the source of truth for build targets.
- `config/` is the source of truth for keymaps, board overlays, and Kconfig options.
- `Makefile` provides local build/upload orchestration (Linux).
- `scripts/build-firmware.ps1` provides local build orchestration (Windows).
- CI behavior is defined in `.github/workflows/build-user-config.yml`.
- External module dependencies are declared in `config/west.yml`.

## Cursor and Copilot rules
- No `.cursorrules` file was found.
- No `.cursor/rules/` directory was found.
- No `.github/copilot-instructions.md` file was found.
- If these files appear later, treat them as higher-priority instructions.

## Environment assumptions
- Set `ZMK_ROOT` to a local ZMK checkout.
- Typical build execution directory is `${ZMK_ROOT}/app`.
- Python venv is expected at `${ZMK_ROOT}/.venv`.
- Required tools: `west`, `yq`, and standard shell tools.
- Upload helpers in Makefile assume Linux-style storage tooling (not available on Windows).
- Treat `C:\ncs\...` toolchain installs as immutable: do not run `pip install`, upgrade packages, or otherwise modify that environment.

## Build, lint, and test commands
There is no dedicated unit-test suite in this repo.
There is no standalone lint pipeline in this repo.
Validation is performed by building the relevant firmware target(s).

### Windows build (primary workflow)
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build-firmware.ps1 -Target left
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build-firmware.ps1 -Target right
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build-firmware.ps1 -Target both
```
Board qualifier: `nice_nano/nrf52840/zmk`. Shield compounds include `nice_view`.

### Windows flash
```powershell
.venv-tools\Scripts\python.exe -I -m nordicsemi dfu serial -pkg scripts\hillside_view_left-nice_nano_nrf52840_zmk-zmk-dfu.zip -p COM27 -b 115200
.venv-tools\Scripts\python.exe -I -m nordicsemi dfu serial -pkg scripts\hillside_view_right-nice_nano_nrf52840_zmk-zmk-dfu.zip -p COM6 -b 115200
```
Flash order: left first, then right. Boot order: left first, wait 5-10s, then right.

### Setup commands (Linux/Makefile)
- `make modules/setup ZMK_ROOT=~/path/to/zmk`
  - Clones external modules from `config/west.yml` into `./modules`.
- `make list`
  - Prints all available build targets parsed from `build.yaml`.

### Build commands (Linux/Makefile)
- Build all: `make all ZMK_ROOT=~/path/to/zmk`
- Hillside left: `make hsv/left ZMK_ROOT=~/path/to/zmk`
- Hillside right: `make hsv/right ZMK_ROOT=~/path/to/zmk`

### Single-test equivalent (most important)
Use a single target build as the equivalent of running one focused test:
- `make build/hillside_view_left-nice_nano ZMK_ROOT=~/path/to/zmk`
- `make build/hillside_view_right-nice_nano ZMK_ROOT=~/path/to/zmk`

### Manual west build (advanced)
Run from `${ZMK_ROOT}/app` with venv activated:

```bash
west build -p -d build/hsv/left -b nice_nano/nrf52840/zmk \
  -- -DSHIELD="hillside_view_left nice_view" \
     -DZMK_CONFIG=/abs/path/to/zmk-config/config \
     -DZMK_EXTRA_MODULES="/abs/path/to/zmk-config/modules/prospector-zmk-module;/abs/path/to/zmk-config/modules/zmk-locales"
```

### Lint/static checks
- No dedicated lint command exists.
- Treat successful `west build` as syntax/compat validation for DTS/keymap/Kconfig edits.
- For YAML edits, optionally run a parse check with `yq`.

### Upload commands (Linux/Makefile)
- `make upload/hillside_view_left-nice_nano ZMK_ROOT=~/path/to/zmk`
- `make upload/hillside_view_right-nice_nano ZMK_ROOT=~/path/to/zmk`

## Code style guidelines

### General editing approach
- Keep edits minimal and tightly scoped to requested behavior.
- Do not reformat unrelated blocks.
- Preserve existing file-local style when a file has mixed conventions.
- Favor explicit, readable configuration over dense clever constructs.

### Includes/imports
- In `.keymap` files, keep includes grouped and stable:
  - behavior includes first,
  - then `dt-bindings`,
  - then input processor includes.
- In overlays/dtsi files, keep binding includes first and local include (`"*.dtsi"`) near top.
- Do not add unused includes.

### Formatting conventions
- Follow indentation already used in touched file (2 or 4 spaces).
- Preserve alignment patterns for matrix maps and `bindings` blocks.
- Prefer one property per line in longer devicetree nodes.
- Keep trailing semicolons and block terminators exact.
- Keep comments short and only for non-obvious hardware/behavior constraints.

### Types and constants
- Use uppercase constants for layer indexes (`DEF`, `SYM`, `NUM`, etc.).
- Use explicit timing constants in milliseconds (`*_MS`) where practical.
- Keep Kconfig boolean values as `y`/`n`.
- Keep numeric config values as plain integers (no unnecessary quoting).

### Naming conventions
- Use short lowercase labels for custom behaviors (`ht`, `lq`, `hml`, `hmr`).
- Use descriptive node names in snake_case where possible.
- Keep new names consistent with keyboard/side naming already present.
- For build entries, follow existing `shield` and `board` naming patterns.

### Error handling and safety
- Preserve Makefile-style fail-fast checks for invalid targets and missing artifacts.
- Keep error messages actionable and specific.
- Do not mask command failures in build/upload flows.
- Avoid destructive git operations while making code edits.

### Keyboard config specifics
- For keymap changes, update only relevant layers and bindings.
- For trackpad/input-split changes, keep central/peripheral responsibilities clear.
- For conditional layers, maintain explicit `if-layers` and `then-layer` intent.
- Keep combo timeouts and hold-tap settings explicit and near related behavior nodes.

### Build matrix and module changes
- Add or modify targets in `build.yaml` first.
- Verify target visibility via `make list`.
- If dependencies change, update `config/west.yml` and validate module setup commands.

## Validation expectations
- Keymap-only change: build at least the affected single target.
- Overlay/dtsi change: build all affected variants (left + right).
- Shared config change: build both left and right targets.
- Build matrix change: run `make list` and build new/changed target(s).

## Quick checklist for agents
- Confirm no Cursor/Copilot rule files were added since last scan.
- Identify affected side(s) and layer(s) before editing.
- Apply minimal edits consistent with local formatting and naming.
- Run focused single-target build(s) first.
- Expand to broader builds when changes affect shared paths.
- Report exact commands run and any validation not executed.
