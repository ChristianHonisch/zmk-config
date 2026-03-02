# Bug: Deep Sleep Wake Failure on Central (Left) Half

**Status: RESOLVED (2026-03-02)**

## Root Cause

A hardware jumper on the left half PCB permanently shorts col0 to row3 in
the kscan matrix. This was a QMK-era left/right side detection mechanism
(`SPLIT_HAND_MATRIX_GRID`). ZMK does not use it -- side detection is
compile-time via Kconfig/shield name.

The permanently closed jumper means `zmk_debounce_is_active()` always
returns true for position (3,0), so the kscan driver never exits scan mode
and never calls `kscan_matrix_read_end()` -> `kscan_matrix_interrupt_enable()`.
As a result:

- Column outputs are never all set HIGH (they are scanned one-at-a-time)
- GPIO SENSE_HIGH is never configured on the row input pins
- `sys_poweroff()` is called with no SENSE -> no wake possible

The right half has no such jumper, so it returns to interrupt-wait mode
normally and wakes correctly.

**Fix: Open (desolder/cut) the jumper at col0/row3 on the left half PCB.**
Position RC(3,0) is not mapped in the matrix transform, so removing the
jumper has zero effect on the keymap.

## Problem

The left (central) half of the Hillside View split keyboard did not wake
from deep sleep (System OFF) on keypress. The right (peripheral) half woke
correctly. Both halves use identical hardware (nice!nano v2 / nRF52840) and
the same kscan matrix driver.

## Related

- ZMK GitHub issue #3207 -- similar symptoms but may be a different issue.
  Our bug was hardware-specific (jumper), not a Zephyr 4.1 regression.

## Hardware

- Board: nice!nano v2 (nRF52840)
- Shield: hillside_view (custom, based on Hillside 46)
- Kscan: col2row matrix, 4 rows x 6 cols per side
- Left columns (outputs): P1.07, P1.15, P1.13, P1.11, P0.10 (NFC2), P0.09 (NFC1)
- Rows (inputs, both halves): P0.11, P1.04, P1.06, P0.02 -- GPIO_ACTIVE_HIGH | GPIO_PULL_DOWN
- Display: nice!view (SPI, ls0xx) -- SPI pins do not overlap kscan
- EXT_POWER: P0.13 (controls external VCC rail, not SoC GPIO power)

## How the kscan wake mechanism works

In col2row mode with interrupt-based scanning:

1. `kscan_matrix_interrupt_enable()` sets all column outputs HIGH and
   configures GPIO_INT_LEVEL_ACTIVE on row inputs
2. The nrfx GPIO driver maps this to PIN_CNF.SENSE = SENSE_HIGH on each
   row pin
3. When `sys_poweroff()` is called, the kscan is skipped (wakeup-source)
   so it stays in interrupt-wait mode with columns HIGH and SENSE configured
4. Pressing a key connects a HIGH column through a diode to a PULL_DOWN row,
   driving the row HIGH, triggering SENSE and waking from System OFF

The jumper broke step 1: the driver never reached interrupt-wait mode because
a "key" was always pressed, keeping it in scan-polling mode.

## Key finding from voltage measurements

In idle mode (interrupt-wait), all column and row pins measure HIGH.
When scanning is active (a key is pressed), columns are driven one-at-a-time
and rows reflect the scan pattern. The left half was always in the scanning
state due to the jumper.

## Confirmed Facts

### sys_poweroff() IS reached

Diagnostic firmware with verbose PM logging confirmed that ALL devices
suspend successfully and `sys_poweroff()` is called. The problem was never
about failing to enter sleep -- it was about failing to wake.

PM suspend log:

| Device           | Result | Meaning                   |
|------------------|--------|---------------------------|
| vbatt            | -88    | -ENOSYS, no PM cb -- OK   |
| temp@4000c000    | -88    | -ENOSYS, no PM cb -- OK   |
| kscan            | SKIP   | wakeup-source -- correct  |
| retention@0 (x2) | -88   | -ENOSYS -- OK             |
| ls0xx@0          | -88    | -ENOSYS -- OK             |
| EXT_POWER        | 0      | Actually suspended -- OK  |
| (USB disconnects) |       | sys_poweroff() called     |

## Ruled Out Causes

These were tested before the jumper was identified as root cause.

- **CONFIG_ZMK_USB=n on left half** -- Did NOT fix wake.
- **Disabling ZMK Studio** -- Did NOT fix wake.
- **Disabling USB logging** -- Did NOT fix wake.
- **NFC pin columns (P0.09, P0.10)** -- Added `&uicr { nfct-pins-as-gpios; }`
  to DTS. Did NOT fix wake (but is the correct config for Zephyr 4.1).
- **zmk_pm_suspend_devices() failure** -- DISPROVED. All devices suspend OK.
- **EXT_POWER cutting kscan GPIO power** -- P0.13 controls external VCC rail,
  not SoC GPIO power.
- **GPIO driver PM callback destroying SENSE** -- gpio_nrfx.c has no PM callback.
- **BLE/clock/SPI/I2C PM callbacks** -- None touch kscan GPIO pins.

## Other fixes applied during investigation

- `config/west.yml`: ZMK pinned to commit `9490391e` (was on `v0.3-branch`
  which pulled Zephyr 3.5/LVGL 8 instead of Zephyr 4.1/LVGL 9)
- `build.yaml`: Board changed to `nice_nano/nrf52840/zmk` (fixes NVS/bonds)
- `hillside_view.dtsi`: Added `&uicr { nfct-pins-as-gpios; }` (proper NFC
  pin config for Zephyr 4.1, replacing silently-ignored Kconfig)

## Diagnostic Patches (for reference)

When diagnostic logging is needed, these patches were used in the ZMK source:

- `app/src/activity.c` -- Added `LOG_INF` calls for sleep entry, suspend result,
  and poweroff; added `k_sleep(K_MSEC(500))` for log flush; commented out
  `!is_usb_power_present()` check to force sleep on USB.
- `app/src/pm.c` -- Added `#include <zephyr/kernel.h>`; added per-device
  `LOG_INF` with skip reasons and suspend results; added `k_sleep(K_MSEC(50))`
  between each device for log flush.
- `config/hillside_view.conf` -- Reduced sleep timeout to 30000ms.
- `scripts/build-firmware.ps1` -- Changed snippet to `zmk-usb-logging`.

These patches MUST be reverted after diagnostic capture. The ZMK source tree
must stay clean.
