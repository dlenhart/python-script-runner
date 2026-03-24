#!/usr/bin/env python3
"""Demo: prints timestamps at intervals."""

import time
from datetime import datetime

def main():
    print("Logging timestamps...")
    for i in range(8):
        now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"  [{now}] Heartbeat {i + 1}/8")
        time.sleep(1)
    print("Timestamp logging complete!")

if __name__ == "__main__":
    main()
