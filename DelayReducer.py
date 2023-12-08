#!/usr/bin/env python

import sys

current_key = None
min_value = float('inf')
max_value = float('-inf')
total_value = 0
count = 0

for line in sys.stdin:
    line = line.strip()
    key, value = line.split("\t")

    # Convert value to float
    value = float(value)

    # Update values for the current key
    if current_key == key:
        min_value = min(min_value, value)
        max_value = max(max_value, value)
        total_value += value
        count += 1
    else:
        # Output results for the previous key
        if current_key:
            average_value = total_value / count
            print(f"{current_key}\t{min_value}\t{max_value}\t{average_value}")

        # Reset values for the new key
        current_key = key
        min_value = value
        max_value = value
        total_value = value
        count = 1

# Output the results for the last key
if current_key:
    average_value = total_value / count
    print(f"{current_key}\t{min_value}\t{max_value}\t{average_value}")
