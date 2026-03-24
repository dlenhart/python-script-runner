#!/usr/bin/env python3
"""Demo: simulates a progress bar."""

import time

def main():
    total = 20
    print("Processing items...")
    for i in range(1, total + 1):
        pct = int(i / total * 100)
        bar = "#" * (pct // 5) + "-" * (20 - pct // 5)
        print(f"  [{bar}] {pct}%  ({i}/{total})")
        time.sleep(0.3)
    print("All items processed!")

if __name__ == "__main__":
    main()
