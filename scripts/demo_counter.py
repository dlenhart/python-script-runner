#!/usr/bin/env python3
"""Demo: counts from 1 to 10."""

import time

def main():
    print("Counting to 10...")
    for i in range(1, 11):
        print(f"  Count: {i}")
        time.sleep(0.5)
    print("Done counting!")

if __name__ == "__main__":
    main()
