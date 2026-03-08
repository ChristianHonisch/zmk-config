#!/usr/bin/env python3
"""Analyze ZMK hold-tap debug logs and produce timing visualizations.

Parses a log file captured by capture-ht-log.py, extracts hold-tap
decision events, and produces a logic-analyzer-style matplotlib timeline
showing key press/release durations, decision points, and captured events.

Usage:
    .venv-tools\\Scripts\\python.exe scripts\\analyze-ht-log.py logs/ht-log-XXXX.log
    .venv-tools\\Scripts\\python.exe scripts\\analyze-ht-log.py logs/ht-log-XXXX.log --save timeline.png
    .venv-tools\\Scripts\\python.exe scripts\\analyze-ht-log.py logs/ht-log-XXXX.log --start 5.0 --end 15.0
"""

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection

# Hillside View position-to-name mapping
POS_NAMES = {
    0: "ESC", 1: "Q", 2: "W", 3: "E", 4: "R", 5: "T",
    6: "Y", 7: "U", 8: "I", 9: "O", 10: "P", 11: "[",
    12: "TAB", 13: "A/LCtrl", 14: "S/LAlt", 15: "D/LShft", 16: "F/LGui", 17: "G",
    18: "H", 19: "J/RGui", 20: "K/RShft", 21: "L/RAlt", 22: ";/RCtrl", 23: "'",
    24: "Z24", 25: "Z", 26: "X", 27: "C", 28: "V", 29: "B",
    30: "N", 31: "M", 32: ",", 33: ".", 34: "-", 35: ".",
    36: "LEnc", 37: "REnc",
    38: "LT1", 39: "LT2/mo1", 40: "LT3/Ret", 41: "LT4/Bksp",
    42: "RT4/Del", 43: "RT3/Spc", 44: "RT2/mo2", 45: "RT1",
}

# Home-row mod positions
HRM_POSITIONS = {13, 14, 15, 16, 19, 20, 21, 22}

# Left-hand and right-hand positions
LEFT_POSITIONS = {0, 1, 2, 3, 4, 5, 12, 13, 14, 15, 16, 17, 24, 25, 26, 27, 28, 29, 36, 38, 39, 40, 41}
RIGHT_POSITIONS = {6, 7, 8, 9, 10, 11, 18, 19, 20, 21, 22, 23, 30, 31, 32, 33, 34, 35, 37, 42, 43, 44, 45}

# Zephyr log timestamp regex: [HH:MM:SS.mmm,uuu]
TS_RE = re.compile(r"\[(\d{2}):(\d{2}):(\d{2})\.(\d{3}),(\d{3})\]")

# Hold-tap log patterns
RE_NEW_UNDECIDED = re.compile(r"(\d+) new undecided hold_tap")
RE_DECIDED = re.compile(r"(\d+) decided (\S+) \((\S+) decision moment (\S+)\)")
RE_CAPTURING = re.compile(r"(\d+) capturing (\d+) (down|up) event")
RE_CLEANUP = re.compile(r"(\d+) cleaning up hold-tap")
RE_BUBBLE = re.compile(r"(\d+) bubble")
RE_RELEASING_POS = re.compile(r"Releasing key position event for position (\d+) (pressed|released)")
RE_HID_KEYCODE = re.compile(r"hid_listener_keycode_(pressed|released): usage_page 0x(\w+) keycode 0x(\w+)")


def parse_timestamp(match) -> float:
    """Convert Zephyr timestamp match to seconds as float."""
    h, m, s, ms, us = (int(x) for x in match.groups())
    return h * 3600 + m * 60 + s + ms / 1000.0 + us / 1_000_000.0


def pos_name(pos: int) -> str:
    """Get human-readable name for a position."""
    return POS_NAMES.get(pos, f"pos{pos}")


def same_hand(pos1: int, pos2: int) -> bool:
    """Check if two positions are on the same hand."""
    return (pos1 in LEFT_POSITIONS and pos2 in LEFT_POSITIONS) or \
           (pos1 in RIGHT_POSITIONS and pos2 in RIGHT_POSITIONS)


@dataclass
class HoldTapEvent:
    """A single hold-tap lifecycle from key-down to cleanup."""
    position: int
    start_time: float = 0.0
    decision_time: float | None = None
    end_time: float | None = None
    status: str = ""           # tap, hold-timer, hold-interrupt
    flavor: str = ""           # balanced, hold-preferred, etc.
    trigger: str = ""          # key-up, other-key-down, other-key-up, timer, quick-tap
    captured_events: list = field(default_factory=list)  # (time, other_pos, direction)
    is_misfire: bool = False


@dataclass
class KeyEvent:
    """A raw key position event (non-HRM)."""
    position: int
    time: float
    direction: str  # "down" or "up"


def parse_log(filepath: str) -> tuple[list[HoldTapEvent], list[KeyEvent]]:
    """Parse a ZMK log file and extract hold-tap events."""
    ht_events: list[HoldTapEvent] = []
    key_events: list[KeyEvent] = []
    active_ht: dict[int, HoldTapEvent] = {}  # pos -> current HT event

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue

            ts_match = TS_RE.search(line)
            if not ts_match:
                continue
            ts = parse_timestamp(ts_match)

            # New undecided hold-tap
            m = RE_NEW_UNDECIDED.search(line)
            if m:
                pos = int(m.group(1))
                evt = HoldTapEvent(position=pos, start_time=ts)
                active_ht[pos] = evt
                ht_events.append(evt)
                continue

            # Decision
            m = RE_DECIDED.search(line)
            if m:
                pos = int(m.group(1))
                if pos in active_ht:
                    ht = active_ht[pos]
                    ht.decision_time = ts
                    ht.status = m.group(2)
                    ht.flavor = m.group(3)
                    ht.trigger = m.group(4)

                    # Misfire detection: hold decision triggered by same-hand key
                    if ht.status in ("hold-interrupt", "hold-timer") and ht.position in HRM_POSITIONS:
                        if ht.captured_events:
                            first_cap = ht.captured_events[0]
                            if same_hand(ht.position, first_cap[1]):
                                ht.is_misfire = True
                continue

            # Capturing another key
            m = RE_CAPTURING.search(line)
            if m:
                ht_pos = int(m.group(1))
                other_pos = int(m.group(2))
                direction = m.group(3)
                if ht_pos in active_ht:
                    active_ht[ht_pos].captured_events.append((ts, other_pos, direction))
                continue

            # Cleanup
            m = RE_CLEANUP.search(line)
            if m:
                pos = int(m.group(1))
                if pos in active_ht:
                    active_ht[pos].end_time = ts
                    del active_ht[pos]
                continue

            # Bubble (non-HT key event)
            m = RE_BUBBLE.search(line)
            if m:
                pos = int(m.group(1))
                key_events.append(KeyEvent(position=pos, time=ts, direction="down"))
                continue

    return ht_events, key_events


def print_summary(ht_events: list[HoldTapEvent]):
    """Print summary statistics to console."""
    if not ht_events:
        print("No hold-tap events found in the log.")
        return

    print(f"\n{'='*70}")
    print(f"HOLD-TAP ANALYSIS SUMMARY")
    print(f"{'='*70}")
    print(f"Total hold-tap events: {len(ht_events)}")

    # By position
    by_pos = defaultdict(list)
    for e in ht_events:
        by_pos[e.position].append(e)

    print(f"\n--- Events by position ---")
    for pos in sorted(by_pos):
        events = by_pos[pos]
        taps = sum(1 for e in events if e.status == "tap")
        holds = sum(1 for e in events if "hold" in e.status)
        misfires = sum(1 for e in events if e.is_misfire)
        avg_ms = 0
        decided = [e for e in events if e.decision_time is not None]
        if decided:
            avg_ms = sum((e.decision_time - e.start_time) * 1000 for e in decided) / len(decided)
        print(f"  {pos_name(pos):>12s}  total={len(events):3d}  tap={taps:3d}  "
              f"hold={holds:3d}  misfire={misfires:3d}  avg_decision={avg_ms:.0f}ms")

    # Misfires
    misfires = [e for e in ht_events if e.is_misfire]
    if misfires:
        print(f"\n--- Probable misfires ({len(misfires)}) ---")
        for e in misfires:
            elapsed = (e.decision_time - e.start_time) * 1000 if e.decision_time else 0
            trigger_info = ""
            if e.captured_events:
                first = e.captured_events[0]
                trigger_info = f" triggered by {pos_name(first[1])} {first[2]}"
            print(f"  {pos_name(e.position):>12s}: {e.status} after {elapsed:.0f}ms "
                  f"({e.trigger}){trigger_info}")

    # Decision time distribution
    decided = [e for e in ht_events if e.decision_time is not None]
    if decided:
        times_ms = [(e.decision_time - e.start_time) * 1000 for e in decided]
        print(f"\n--- Decision time distribution ---")
        buckets = [0, 50, 100, 150, 200, 250, 300, 400, 500, 1000]
        for i in range(len(buckets) - 1):
            count = sum(1 for t in times_ms if buckets[i] <= t < buckets[i + 1])
            bar = "#" * count
            print(f"  {buckets[i]:4d}-{buckets[i+1]:4d}ms: {count:3d} {bar}")
        over = sum(1 for t in times_ms if t >= 1000)
        if over:
            print(f"  1000+   ms: {over:3d} {'#' * over}")

    # Tuning recommendations
    tap_times = [(e.decision_time - e.start_time) * 1000
                 for e in ht_events if e.decision_time and e.status == "tap"]
    hold_times = [(e.decision_time - e.start_time) * 1000
                  for e in ht_events if e.decision_time and "hold" in e.status]
    if tap_times:
        p95 = sorted(tap_times)[int(len(tap_times) * 0.95)]
        print(f"\n--- Tuning suggestions ---")
        print(f"  95th percentile tap decision time: {p95:.0f}ms")
        if p95 < 200:
            print(f"  Your tapping is fast. tapping-term-ms=280 should be comfortable.")
        if misfires:
            cap_deltas = []
            for e in misfires:
                if e.captured_events:
                    cap_deltas.append((e.captured_events[0][0] - e.start_time) * 1000)
            if cap_deltas:
                max_delta = max(cap_deltas)
                print(f"  Fastest misfire inter-key interval: {min(cap_deltas):.0f}ms")
                print(f"  Suggest require-prior-idle-ms >= {int(max_delta) + 20}")


def plot_timeline(ht_events: list[HoldTapEvent], key_events: list[KeyEvent],
                  start_s: float | None = None, end_s: float | None = None,
                  save_path: str | None = None):
    """Create a logic-analyzer style timeline plot."""
    if not ht_events:
        print("No hold-tap events to plot.")
        return

    # Determine time range
    all_times = [e.start_time for e in ht_events]
    if ht_events[0].end_time:
        all_times.append(max(e.end_time for e in ht_events if e.end_time))
    t_min = min(all_times)
    t_max = max(all_times)

    if start_s is not None:
        t_min = t_min + start_s if start_s < t_min else start_s
    if end_s is not None:
        t_max = t_min + end_s if end_s < t_max else end_s

    # Filter events in time range
    ht_in_range = [e for e in ht_events if e.start_time >= t_min - 0.5 and e.start_time <= t_max + 0.5]

    if not ht_in_range:
        print(f"No hold-tap events in the time range {t_min:.1f}s - {t_max:.1f}s")
        return

    # Collect all positions involved
    positions_seen = set()
    for e in ht_in_range:
        positions_seen.add(e.position)
        for _, other_pos, _ in e.captured_events:
            positions_seen.add(other_pos)

    # Sort positions: HRM positions first (by number), then others
    pos_order = sorted(positions_seen, key=lambda p: (0 if p in HRM_POSITIONS else 1, p))
    pos_to_lane = {p: i for i, p in enumerate(pos_order)}
    n_lanes = len(pos_order)

    # Create figure
    fig, ax = plt.subplots(figsize=(max(14, (t_max - t_min) * 4), max(4, n_lanes * 0.6 + 2)))

    # Colors
    COLOR_TAP = "#4CAF50"        # green
    COLOR_HOLD = "#F44336"       # red
    COLOR_HOLD_OK = "#FF9800"    # orange (intentional hold)
    COLOR_CAPTURED = "#90CAF9"   # light blue
    COLOR_UNDECIDED = "#FFEB3B"  # yellow

    bar_height = 0.6

    for evt in ht_in_range:
        lane = pos_to_lane[evt.position]
        t0 = (evt.start_time - t_min) * 1000  # convert to ms relative

        # End time
        t_end = ((evt.end_time or evt.decision_time or evt.start_time) - t_min) * 1000
        t_dec = ((evt.decision_time or evt.start_time) - t_min) * 1000

        # Undecided phase (key-down to decision)
        undecided_width = t_dec - t0
        if undecided_width > 0:
            rect = mpatches.FancyBboxPatch(
                (t0, lane - bar_height / 2), undecided_width, bar_height,
                boxstyle="round,pad=0.5", facecolor=COLOR_UNDECIDED, edgecolor="black",
                linewidth=0.8, alpha=0.7)
            ax.add_patch(rect)

        # Decided phase (decision to cleanup)
        decided_width = t_end - t_dec
        if decided_width > 0 and evt.status:
            if evt.is_misfire:
                color = COLOR_HOLD
            elif evt.status == "tap":
                color = COLOR_TAP
            elif "hold" in evt.status:
                color = COLOR_HOLD_OK
            else:
                color = COLOR_TAP

            rect = mpatches.FancyBboxPatch(
                (t_dec, lane - bar_height / 2), max(decided_width, 2), bar_height,
                boxstyle="round,pad=0.5", facecolor=color, edgecolor="black",
                linewidth=0.8, alpha=0.9)
            ax.add_patch(rect)

        # Decision point marker
        if evt.decision_time:
            ax.axvline(x=t_dec, ymin=(lane - 0.3) / n_lanes, ymax=(lane + 0.3) / n_lanes,
                       color="black", linewidth=1.5, linestyle="--", alpha=0.5)

            # Annotation
            elapsed_ms = (evt.decision_time - evt.start_time) * 1000
            label = f"{evt.status}\n{elapsed_ms:.0f}ms"
            if evt.is_misfire:
                label += "\nMISFIRE"
            ax.annotate(label, xy=(t_dec, lane + bar_height / 2 + 0.05),
                        fontsize=6, ha="center", va="bottom",
                        color="red" if evt.is_misfire else "black")

        # Captured events — draw small markers on other lanes
        for cap_time, cap_pos, cap_dir in evt.captured_events:
            if cap_pos in pos_to_lane:
                cap_lane = pos_to_lane[cap_pos]
                cap_t = (cap_time - t_min) * 1000
                marker = "v" if cap_dir == "down" else "^"
                ax.plot(cap_t, cap_lane, marker=marker, color=COLOR_CAPTURED,
                        markersize=8, markeredgecolor="black", markeredgewidth=0.5, zorder=5)

    # Tapping-term reference line (280ms from each HT start)
    for evt in ht_in_range:
        t0 = (evt.start_time - t_min) * 1000
        lane = pos_to_lane[evt.position]
        ax.plot(t0 + 280, lane, marker="|", color="gray", markersize=12,
                markeredgewidth=1, alpha=0.4)

    # Y-axis: position names
    ax.set_yticks(range(n_lanes))
    ax.set_yticklabels([pos_name(p) for p in pos_order], fontsize=9, fontfamily="monospace")
    ax.set_ylim(-0.5, n_lanes - 0.5)
    ax.invert_yaxis()

    # X-axis
    ax.set_xlabel("Time (ms)", fontsize=10)
    ax.set_title("ZMK Hold-Tap Timeline (Logic Analyzer View)", fontsize=12, fontweight="bold")

    # Grid
    ax.grid(axis="x", alpha=0.3, linestyle=":")
    ax.grid(axis="y", alpha=0.1)

    # Legend
    legend_patches = [
        mpatches.Patch(color=COLOR_UNDECIDED, alpha=0.7, label="Undecided"),
        mpatches.Patch(color=COLOR_TAP, alpha=0.9, label="Tap"),
        mpatches.Patch(color=COLOR_HOLD_OK, alpha=0.9, label="Hold (intentional)"),
        mpatches.Patch(color=COLOR_HOLD, alpha=0.9, label="Hold (MISFIRE)"),
        plt.Line2D([0], [0], marker="v", color=COLOR_CAPTURED, markersize=8,
                   linestyle="None", markeredgecolor="black", label="Captured key-down"),
        plt.Line2D([0], [0], marker="^", color=COLOR_CAPTURED, markersize=8,
                   linestyle="None", markeredgecolor="black", label="Captured key-up"),
        plt.Line2D([0], [0], marker="|", color="gray", markersize=12,
                   linestyle="None", label="Tapping-term (280ms)"),
    ]
    ax.legend(handles=legend_patches, loc="upper right", fontsize=7, framealpha=0.9)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Timeline saved to {save_path}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Analyze ZMK hold-tap debug logs and produce timing visualizations")
    parser.add_argument("logfile", help="Path to log file from capture-ht-log.py")
    parser.add_argument("--save", "-s", help="Save timeline to image file instead of showing")
    parser.add_argument("--start", type=float, default=None,
                        help="Start time in seconds (relative to first event)")
    parser.add_argument("--end", type=float, default=None,
                        help="End time in seconds (relative to first event)")
    parser.add_argument("--no-plot", action="store_true", help="Skip plot, only print summary")
    args = parser.parse_args()

    print(f"Parsing {args.logfile}...")
    ht_events, key_events = parse_log(args.logfile)

    print_summary(ht_events)

    if not args.no_plot:
        plot_timeline(ht_events, key_events,
                      start_s=args.start, end_s=args.end,
                      save_path=args.save)


if __name__ == "__main__":
    main()
