# AGENTS.md
Guidance for coding agents operating in this repository.
This repository is a ZMK firmware config workspace for split keyboards.
Primary keyboard is Hillside View.

## Scope and source of truth
- `build.yaml` is the source of truth for build targets.
- `config/` is the source of truth for keymaps, board overlays, and Kconfig options.
- `Makefile` provides local build/upload orchestration.
- CI behavior is defined in `.github/workflows/build-user-config.yml`.
- External module dependencies are declared in `config/west.yml`.

## Private information
- Store private or machine-specific information that must not be published, such as MAC addresses, adapter IDs, host identifiers, local paths with personal data, and trace details, only under `secrets/`.
- `secrets/` is intentionally ignored by Git and must never be committed, quoted into public docs, issue reports, commit messages, or logs intended for GitHub.
- Public docs may refer to sanitized placeholders such as `<PC_BT_MAC>` or `<keyboard_addr>`.
- If private information is already present in tracked docs, move it to `secrets/` and replace it with a sanitized placeholder.

## Important repository docs
- `README.md` provides a high-level repository and keyboard overview.
- `build-instructions.md` is the authoritative local build procedure and build verification guide.
- `flashing-instructions.md` is the authoritative flashing/reset procedure and post-flash validation guide.
- `SCRIPT-INFO.md` summarizes available scripts, parameters, and typical workflows.
- `TODO.md` is the current backlog for follow-up work; treat it as task context, not policy.
- `KNOWLEDGE.md` collects troubleshooting knowledge for BLE, bonding, build history, and flash-order issues; some details are machine-specific.
- `bt-disconnect-error.md` contains the current Bluetooth disconnect investigation history and evidence.
- `temporary_changes.md` tracks temporary diagnostic changes that should usually be reverted after debugging.
- `docs/bug-deep-sleep-wake.md` documents the resolved deep-sleep wake bug, its root cause, and ruled-out approaches.

### Topic-specific expert knowledge files
- The repository contains expert-level knowledge files for specific topics. Do not read them by default for every task, but if the current task touches a topic covered by one of these files, you SHALL read the relevant file(s) before making recommendations, interpreting evidence, or changing code/config related to that topic.
- Read `KNOWLEDGE.md` for BLE, bonding, build history, flash order, and machine-specific troubleshooting topics.
- Read `bt-disconnect-error.md` for Bluetooth disconnect, reconnect storm, timeout, stuck-key, ETW, or host interoperability investigation work.
- Read `temporary_changes.md` when working on diagnostics, USB logging, temporary overrides, or reversion of debug-only changes.
- Read `docs/bug-deep-sleep-wake.md` when working on sleep, wake, poweroff, or related regressions.
- If multiple expert knowledge files apply, read all relevant ones. Treat them as required topic context, not optional background.

The following Markdown files are generally session-specific or archival and should not be treated as primary guidance unless the task explicitly calls for historical context: `STATUS.md`, `relevant-files-dirs.md`, `.opencode/plans/*.md`, and most of `bugs_to_fix.md`.

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
- Upload helpers in Makefile assume Linux-style storage tooling.
- Treat `C:\ncs\...` toolchain installs as immutable: do not run `pip install`, upgrade packages, or otherwise modify that environment.

## Build, lint, and test commands
There is no dedicated unit-test suite in this repo.
There is no standalone lint pipeline in this repo.
Validation is performed by building the relevant firmware target(s).

### Setup commands
- `make modules/setup ZMK_ROOT=~/path/to/zmk`
  - Clones external modules from `config/west.yml` into `./modules`.
- `make list`
  - Prints all available build targets parsed from `build.yaml`.

### Build commands
- Build all: `make all ZMK_ROOT=~/path/to/zmk`
- Hillside group: `make hsv/all ZMK_ROOT=~/path/to/zmk`
- Hillside left: `make hsv/left ZMK_ROOT=~/path/to/zmk`
- Hillside right: `make hsv/right ZMK_ROOT=~/path/to/zmk`

### Single-test equivalent (most important)
Use a single target build as the equivalent of running one focused test:
- `make build/hillside_view_left-nice_nano ZMK_ROOT=~/path/to/zmk`
- `make build/hillside_view_right-nice_nano ZMK_ROOT=~/path/to/zmk`

### Manual west build (advanced)
Run from `${ZMK_ROOT}/app` with venv activated:

```bash
west build -p -d build/hsv/left -b nice_nano \
  -- -DSHIELD="hillside_view_left" \
     -DZMK_CONFIG=/abs/path/to/zmk-config/config \
     -DZMK_EXTRA_MODULES="/abs/path/to/zmk-config/modules/prospector-zmk-module"
```

### Lint/static checks
- No dedicated lint command exists.
- Treat successful `west build` as syntax/compat validation for DTS/keymap/Kconfig edits.
- For YAML edits, optionally run a parse check with `yq`.

### Upload commands
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
- Overlay/dtsi change: build all affected variants for that keyboard.
- Shared config change: build both Hillside targets.
- Build matrix change: run `make list` and build new/changed target(s).

## Quick checklist for agents
- Confirm no Cursor/Copilot rule files were added since last scan.
- Identify affected side(s) and layer(s) before editing.
- Apply minimal edits consistent with local formatting and naming.
- Run focused single-target build(s) first.
- Expand to broader builds when changes affect shared paths.
- Report exact commands run and any validation not executed.
