#!/usr/bin/env python

import sys

for line in sys.stdin:
    line = line.strip()
    fields = line.split(",")

    # Extract relevant columns
    UniqueCarrier = fields[8].strip()
    Origin = fields[16].strip()
    TaxiIn = float(fields[19].strip())
    ArrDelay = float(fields[14].strip())
    # Ignore rows with missing values
    if 'NA' in [UniqueCarrier, Origin, TaxiIn, ArrDelay]:
        continue
    # Create compound key
    key = "-".join([UniqueCarrier, Origin])
    # Emit key-value pairs
    print(f"{key}\t{TaxiIn + ArrDelay}")
