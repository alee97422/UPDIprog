#!/usr/bin/env python3

import subprocess
import glob
import sys
import os
import platform
import re

def usage():
    print("Usage: python flash_sao.py firmware.hex")
    sys.exit(1)

def detect_ch340_port():
    system = platform.system()

    if system == "Linux":
        ports = glob.glob("/dev/ttyUSB*")
        for port in ports:
            try:
                info = subprocess.check_output(["udevadm", "info", "-q", "all", "-n", port], text=True)
                if "CH340" in info or "1a86:7523" in info:
                    return port
            except Exception:
                continue

    elif system == "Darwin":  # macOS
        ports = glob.glob("/dev/tty.wchusbserial*") + glob.glob("/dev/cu.wchusbserial*")
        if ports:
            return ports[0]

    elif system == "Windows":
        try:
            output = subprocess.check_output(["wmic", "path", "Win32_SerialPort"], text=True)
            matches = re.findall(r"(COM\d+).*CH340", output, re.IGNORECASE)
            if matches:
                return matches[0]
        except Exception:
            return None

    return None


def run_cmd(label, cmd):
    print(label)
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print("Error during:", label)
        return False
    return True

def wait_for_enter():
    input("Press ENTER to continue...")

def flash_cycle(firmware):
    while True:
        port = detect_ch340_port()
        if not port:
            print("No CH340 device found.")
            wait_for_enter()
            continue

        print("Using port:", port)
        if not run_cmd("ping", ["pymcuprog", "ping", "-t", "uart", "-u", port, "-d", "attiny1616"]):
            wait_for_enter()
            continue

        wait_for_enter()

        run_cmd("erase", ["pymcuprog", "erase", "-t", "uart", "-u", port, "-d", "attiny1616"])
        run_cmd("write", ["pymcuprog", "write", "-t", "uart", "-u", port, "-d", "attiny1616", "-f", firmware])

        print("Done.")
        wait_for_enter()

if __name__ == "__main__":
    if len(sys.argv) != 2 or not sys.argv[1].endswith(".hex"):
        usage()

    firmware = sys.argv[1]
    if not os.path.isfile(firmware):
        print("File not found:", firmware)
        sys.exit(1)

    flash_cycle(firmware)
