# BT Disconnect Error

## Evidence Summary

### Observed behavior
- Disconnects cluster shortly after the keyboard wakes from sleep.
- The first few minutes after wake are unstable; later the connection becomes stable.
- Stuck keys can occur during these outages, including `Space`, `c`, and a stuck HRM/Ctrl state.
- The keyboard is stable on other hosts.
- Other Bluetooth devices are stable on this Mediatek laptop.

### Keyboard-side evidence
- In ZMK USB logs, keys are often processed correctly immediately before failure.
- Example: `Space` shows a clean press and release in firmware logs before the outage.
- Then there is a silent gap in logging.
- After the gap, BLE reconnect is logged.
- This means the stuck key is not explained by a bad physical press or an obviously missing release in normal key processing.

### Windows ETW evidence
From `logs/bt-etl.txt`:

1. **Real host-side BLE disconnect**
- `logs/bt-etl.txt:80`
- `HciDisconnectResult` at `35.179359700s`
- disconnect reason field is `8`
- earlier raw HCI decoding strongly suggests this is **`0x08 Connection Timeout`**

2. **Windows immediately removes the keyboard HID interfaces**
- `logs/bt-etl.txt:44-47`
- HID `Col01` and `Col02` removal queued/started at about `35.1827s`

3. **Windows says the device was surprise removed**
- `logs/bt-etl.txt:61-64`
- both HID collections were:
  - "reported as missing on the bus"

4. **Windows then reconnects and rebuilds the HID stack**
- `logs/bt-etl.txt:79`
  - `HciConnectResult` at `35.787354500s`
- `logs/bt-etl.txt:24-41`
  - `ProcessNewDevice`, `DeviceAdd`, `kbdhid`, `kbdclass`
- `logs/bt-etl.txt:57-58`
  - device start completes successfully again

### Interpreted failure sequence
Most likely sequence for the captured outage:

1. Keyboard wakes and enters an unstable reconnect phase
2. BLE link degrades
3. Host controller reports **connection timeout**
4. Windows surprise-removes the keyboard HID device
5. During the teardown/rebuild window, stale key state can remain active long enough to auto-repeat
6. BLE reconnect succeeds
7. HID stack is rebuilt and the stuck key clears

### What this rules out
Weakens these explanations:
- bad physical key press
- simple missed key scan
- ordinary long key hold
- purely cosmetic display disconnect
- Windows inventing the disconnect without a real BLE failure

### What remains plausible
Still plausible root causes:
1. host-device BLE interoperability issue during wake/reconnect
2. left-half instability during simultaneous host-BLE and split-BLE recovery
3. timeout-driven reconnect storm in the keyboard wake window
4. Mediatek-specific or pair-specific host behavior
5. RF/interference as a contributing factor, though the repeatable wake timing suggests state/timing is more important than random interference

### Updated observation after re-pair

A later test weakened the "only immediately after wake" theory.

Observed:
- A disconnect occurred about 35 minutes after wake.
- This had not happened before in that form.
- A stuck key happened immediately with that disconnect.
- Another disconnect followed later.
- The second delay may have been around 30s, but that timing was not confirmed.

Interpretation:
- Re-pair did not hold as a fix.
- The failure may not be limited to the first few minutes after wake.
- Possible explanations:
  1. there are two failure modes: an early wake-time reconnect storm and a later spontaneous timeout
  2. or the same timeout-driven mechanism can occur both shortly after wake and later during normal operation

### Split-disabled test

Observed:
- A test was performed with split/right-half involvement disabled or absent.
- The host BLE disconnect still occurred.

Interpretation:
- This weakens split BLE as the primary cause of the initial host connection timeout.
- Split-central cleanup warnings may still affect post-disconnect recovery when split is enabled, but they do not explain the first disconnect by themselves.

## Synchronized Capture: 2026-04-19 21:19:41

Files:
- `logs/synchronous-log-20260419-211941.log`
- `logs/synchronous-log-20260419-211941.etl`

### Keyboard-side sequence
- Disconnect at `00:00:25.336`
- Reconnect at `00:00:29.627`
- Outage duration on keyboard side: about `4.29s`

Important lines:
- `logs/synchronous-log-20260419-211941.log:22`
  - `split_central_disconnected ... reason 34`
- `logs/synchronous-log-20260419-211941.log:23`
  - `Failed to release peripheral slot (-22)`
- `logs/synchronous-log-20260419-211941.log:25`
  - host disconnect `reason 0x22`
- `logs/synchronous-log-20260419-211941.log:28`
  - `Got battery level event for an out of range peripheral index`
- `logs/synchronous-log-20260419-211941.log:35`
  - endpoint changed to `USB`
- `logs/synchronous-log-20260419-211941.log:50`
  - endpoint changed back to `BLE:0`

### ETW-side sequence
- `HciDisconnectResult` with reason `8` again, strongly consistent with BLE connection timeout
- Windows marks the keyboard disconnected
- HID collections are torn down and rebuilt
- A later PnP churn cluster continues after reconnect, matching the observed temporary high `explorer.exe` CPU

### Interpretation
- This synchronized capture shows the same timeout-driven host disconnect pattern as earlier captures.
- It also shows split-central disconnect handling and split bookkeeping warnings at the same time.
- This strengthens the idea that the left half is getting into a bad state affecting both BLE roles:
  - host BLE peripheral role
  - split BLE central role
- The later Windows PnP churn likely explains why `explorer.exe` remains busy even after the keyboard appears reconnected.

### Current ZMK version context
- Current ZMK: `9490391e1e4010c83291d437b7f9a71ace244581`
- Describe: `v0.3-92-g9490391e`
- Zephyr: `4.1.0`
- No obvious recent ZMK release-note item was found that clearly fixes this exact wake/reconnect timeout issue.

## Recommended next steps

1. Use this summary as the basis for a ZMK issue report.
2. On the next outage, capture both:
   - left USB log
   - Windows ETW trace
3. Compare whether every outage shows:
   - HCI disconnect reason `0x08`
   - surprise removal
   - reconnect within ~0.6s
4. If you want to keep investigating before filing:
   - inspect ZMK disconnect/endpoint-clear code paths
   - check whether the left half fails to log disconnect handling during the silent gap

## Draft issue framing

A concise issue title would be:

- `Windows Mediatek host: split keyboard enters wake-time reconnect storm with HCI disconnect reason 0x08 and stale stuck keys`

And the key claim would be:

- after keyboard wake, the BLE connection repeatedly times out on Windows
- ETW shows host-side `HciDisconnectResult` with reason `0x08`
- Windows surprise-removes and rebuilds the HID device
- stale key state can persist during the teardown/reconnect window
- the same keyboard is stable on other hosts, while this laptop is stable with other BT devices, suggesting a pair-specific interoperability issue
