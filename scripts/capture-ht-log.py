#!/usr/bin/env python3
"""Capture ZMK USB serial log output for hold-tap diagnostics.

Connects to the keyboard's USB CDC ACM serial port, records all output
to a timestamped log file, and shows a live filtered preview of hold-tap
related messages on the console.

Usage:
    .venv-tools\\Scripts\\python.exe scripts\\capture-ht-log.py [--port COM5]

Press Ctrl+C to stop recording.
"""

import argparse
import datetime
import os
import re
import sys
import time

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


def is_ht_line(line: str) -> bool:
    """Check if a log line is related to hold-tap behavior."""
    return any(p.search(line) for p in HT_PATTERNS)


def find_usb_serial_port() -> str | None:
    """Auto-detect the USB serial COM port (skip Bluetooth ports)."""
    for port in serial.tools.list_ports.comports():
        desc = (port.description or "").lower()
        # Skip Bluetooth serial ports
        if "bluetooth" in desc:
            continue
        # Match USB serial devices
        if "usb" in desc or "seriell" in desc.lower():
            # Skip known right-half bootloader port
            return port.device
    return None


def main():
    parser = argparse.ArgumentParser(description="Capture ZMK hold-tap debug logs")
    parser.add_argument("--port", "-p", help="COM port (auto-detected if omitted)")
    parser.add_argument("--baud", "-b", type=int, default=115200, help="Baud rate")
    parser.add_argument("--output-dir", "-o", default="logs", help="Output directory")
    args = parser.parse_args()

    # Find port
    port = args.port
    if not port:
        port = find_usb_serial_port()
        if not port:
            print("ERROR: No USB serial port found. Is the keyboard connected via USB?")
            print("Available ports:")
            for p in serial.tools.list_ports.comports():
                print(f"  {p.device}: {p.description}")
            sys.exit(1)

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Generate log filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = os.path.join(args.output_dir, f"ht-log-{timestamp}.log")

    print(f"Connecting to {port} at {args.baud} baud...")
    print(f"Recording to {log_path}")
    print(f"Showing hold-tap related lines in real-time.")
    print(f"Press Ctrl+C to stop.\n")

    total_lines = 0
    ht_lines = 0
    start_time = time.time()

    try:
        with serial.Serial(port, args.baud, timeout=1) as ser, \
             open(log_path, "w", encoding="utf-8") as log_file:

            # Write header
            log_file.write(f"# ZMK Hold-Tap Log Capture\n")
            log_file.write(f"# Port: {port}\n")
            log_file.write(f"# Started: {datetime.datetime.now().isoformat()}\n")
            log_file.write(f"#\n")
            log_file.flush()

            while True:
                try:
                    raw = ser.readline()
                    if not raw:
                        continue

                    line = raw.decode("utf-8", errors="replace").rstrip()
                    if not line:
                        continue

                    total_lines += 1
                    log_file.write(line + "\n")

                    # Flush every 100 lines to avoid data loss
                    if total_lines % 100 == 0:
                        log_file.flush()

                    # Show hold-tap related lines on console
                    if is_ht_line(line):
                        ht_lines += 1
                        # Color code: red for hold decisions, green for taps
                        if "decided hold" in line or "decided hold-interrupt" in line:
                            print(f"\033[91m{line}\033[0m")  # red
                        elif "decided tap" in line:
                            print(f"\033[92m{line}\033[0m")  # green
                        else:
                            print(f"\033[90m{line}\033[0m")  # gray

                except serial.SerialException as e:
                    print(f"\nSerial error: {e}")
                    break

    except KeyboardInterrupt:
        pass
    except serial.SerialException as e:
        print(f"ERROR: Could not open {port}: {e}")
        sys.exit(1)

    duration = time.time() - start_time
    print(f"\n--- Recording stopped ---")
    print(f"Duration:       {duration:.1f}s")
    print(f"Total lines:    {total_lines}")
    print(f"Hold-tap lines: {ht_lines}")
    print(f"Log saved to:   {log_path}")


if __name__ == "__main__":
    main()
