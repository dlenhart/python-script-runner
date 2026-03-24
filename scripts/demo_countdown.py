#!/usr/bin/env python3
"""Demo: countdown from 10 to liftoff."""

import time

def main():
    print("Initiating countdown...")
    for i in range(10, 0, -1):
        print(f"  T-{i}...")
        time.sleep(0.8)
    print("Liftoff!")

if __name__ == "__main__":
    main()
