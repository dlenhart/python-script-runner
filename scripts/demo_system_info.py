#!/usr/bin/env python3
"""Demo: gathers and displays system info."""

import os
import platform
import sys
import time

def main():
    info = [
        ("Platform", platform.system()),
        ("OS Version", platform.version()),
        ("Machine", platform.machine()),
        ("Python Version", sys.version.split()[0]),
        ("Python Path", sys.executable),
        ("Working Directory", os.getcwd()),
        ("User", os.getenv("USER", "unknown")),
        ("CPU Count", str(os.cpu_count())),
    ]

    print("Gathering system information...\n")
    for label, value in info:
        print(f"  {label}: {value}")
        time.sleep(0.6)
    print("\nSystem info gathered!")

if __name__ == "__main__":
    main()
