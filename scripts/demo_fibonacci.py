#!/usr/bin/env python3
"""Demo: generates Fibonacci numbers."""

import time

def main():
    print("Generating Fibonacci sequence...")
    a, b = 0, 1
    for i in range(15):
        print(f"  F({i}) = {a}")
        a, b = b, a + b
        time.sleep(0.4)
    print("Sequence complete!")

if __name__ == "__main__":
    main()
