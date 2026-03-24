"""Demo script that fails on purpose to test the error tab indicator."""

import sys
import time

print("Starting demo_fail...")
time.sleep(1)
print("About to crash intentionally...")
time.sleep(0.5)
print("Raising exception now.")
sys.exit(1)
