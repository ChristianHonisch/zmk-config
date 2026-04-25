#!/usr/bin/env python3
"""Capture ZMK USB serial log output from both keyboard halves.

Connects to both keyboard halves via USB CDC ACM serial ports, records all
output to a timestamped log file with side identifiers (L/R), and shows a
live filtered preview of hold-tap related messages on the console.

Usage:
    .venv-tools\\Scripts\\python.exe scripts\\capture-ht-log-both.py

Press Ctrl+C to stop recording.
"""

import argparse
import datetime
import os
import re
import sys
import time
import threading

import serial
import serial.tools.list_ports


# Patterns that indicate hold-tap related log lines
HT_PATTERNS = [
    re.compile(r"hold_tap"),
    re.compile(r"\bdecided\b"),
    re.compile(r"\bcapturing\b.*\bevent\b"),
    re.compile(r"\bbubbl"),
    re.compile(r"\bcleaning up\b"),
    re.compile(r"\bundecided\b"),
    re.compile(r"hid_listener_keycode"),
    re.compile(r"Releasing.*event"),
]

# Patterns to identify which half sent the data
SIDE_PATTERNS = {
    "L": [
        re.compile(r"kscan_matrix_read"),  # Left half matrix scanner
        re.compile(r"vddh_sample"),  # Left half battery (VDDH)
    ],
    "R": [
        re.compile(r"split_central"),  # Right half via BLE central
        re.compile(r"peripheral_"),  # Peripheral (right half) events
    ],
}


def is_ht_line(line: str) -> bool:
    """Check if a log line is related to hold-tap behavior."""
    return any(p.search(line) for p in HT_PATTERNS)


def detect_side(line: str) -> str:
    """Detect which half (L/R) the log line came from."""
    for side, patterns in SIDE_PATTERNS.items():
        for p in patterns:
            if p.search(line):
                return side
    return "?"  # Unknown/merged


# Default ports for this machine
DEFAULT_LEFT_PORT = "COM5"
DEFAULT_RIGHT_PORT = "COM3"


def find_usb_serial_ports() -> list[tuple[str, str]]:
    """Auto-detect USB serial COM ports (skip Bluetooth ports)."""
    ports = []
    for port in serial.tools.list_ports.comports():
        desc = (port.description or "").lower()
        # Skip Bluetooth serial ports
        if "bluetooth" in desc:
            continue
        # Match USB serial devices
        if "usb" in desc or "seriell" in desc.lower():
            ports.append((port.device, desc))
    return ports


def reader_thread(
    port: str,
    baud: int,
    log_file,
    lock: threading.Lock,
    stop_event: threading.Event,
    port_label: str,
):
    """Read from a serial port, write to log file, and show hold-tap lines on console."""
    try:
        with serial.Serial(port, baud, timeout=1) as ser:
            while not stop_event.is_set():
                try:
                    raw = ser.readline()
                    if not raw:
                        continue

                    line = raw.decode("utf-8", errors="replace").rstrip()
                    if not line:
                        continue

                    # Determine which side
                    side = detect_side(line)
                    if side == "?":
                        side = port_label

                    # Write to file with side prefix
                    with lock:
                        log_file.write(f"[{side}] {line}\n")
                        log_file.flush()

                    # Show hold-tap related lines on console
                    if is_ht_line(line):
                        if "decided hold" in line or "decided hold-interrupt" in line:
                            print(f"\033[91m[{side}] {line}\033[0m")  # red
                        elif "decided tap" in line:
                            print(f"\033[92m[{side}] {line}\033[0m")  # green
                        else:
                            print(f"\033[90m[{side}] {line}\033[0m")  # gray

                except serial.SerialException:
                    break
                except Exception:
                    pass
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(
        description="Capture ZMK hold-tap debug logs from both halves"
    )
    parser.add_argument("--baud", "-b", type=int, default=115200, help="Baud rate")
    parser.add_argument("--output-dir", "-o", default="logs", help="Output directory")
    parser.add_argument(
        "--output-file",
        help="Explicit output file path (overrides generated filename)",
    )
    parser.add_argument(
        "--stop-file",
        help="Exit when this file appears on disk",
    )
    parser.add_argument(
        "--left", "-l", help="Left half COM port (auto-detected if omitted)"
    )
    parser.add_argument(
        "--right", "-r", help="Right half COM port (auto-detected if omitted)"
    )
    args = parser.parse_args()

    # Use default ports unless overridden
    left_port = args.left or DEFAULT_LEFT_PORT
    right_port = args.right or DEFAULT_RIGHT_PORT

    print(f"Using ports:")
    print(f"  Left:  {left_port}")
    print(f"  Right: {right_port}")

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Generate log filename
    if args.output_file:
        log_path = args.output_file
        parent = os.path.dirname(log_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
    else:
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        log_path = os.path.join(args.output_dir, f"ht-log-{timestamp}.log")

    print(f"Connecting to both halves at {args.baud} baud...")
    print(f"Recording to {log_path}")
    print(f"Showing hold-tap related lines in real-time.")
    print(f"Press Ctrl+C to stop.\n")

    start_time = time.time()
    stop_event = threading.Event()
    lock = threading.Lock()
    threads = []

    try:
        with open(log_path, "w", encoding="utf-8") as log_file:
            # Write header
            log_file.write(f"# ZMK Dual Half Log Capture\n")
            log_file.write(f"# Left:  {left_port}\n")
            log_file.write(f"# Right: {right_port}\n")
            log_file.write(f"# Started: {datetime.datetime.now().isoformat()}\n")
            log_file.write(
                f"# Side markers: [L]=Left half, [R]=Right half, [?]=Unknown\n"
            )
            log_file.write(f"#\n")
            log_file.flush()

            # Start reader threads
            threads = []
            port_labels = {"left_port": "L", "right_port": "R"}
            for port, label in [(left_port, "L"), (right_port, "R")]:
                t = threading.Thread(
                    target=reader_thread,
                    args=(port, args.baud, log_file, lock, stop_event, label),
                )
                t.daemon = True
                t.start()
                threads.append(t)

            # Wait for threads to run (they handle logging and console output)
            while not stop_event.is_set():
                try:
                    if args.stop_file and os.path.exists(args.stop_file):
                        stop_event.set()
                        break
                    time.sleep(0.5)
                except KeyboardInterrupt:
                    break

    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        # Wait for threads to finish
        for t in threads:
            t.join(timeout=1)

    duration = time.time() - start_time
    print(f"\n--- Recording stopped ---")
    print(f"Duration:       {duration:.1f}s")
    print(f"Log saved to:   {log_path}")


if __name__ == "__main__":
    main()
