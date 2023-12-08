

#! /usr/bin/env python
import sys
last_key = None
count = 0
min_value = float('inf')
max_value = float('-inf')
# total_value = 0
sum = 1



# keys come grouped together so we need to keep track of state a little bit  thus when the key changes, 
# we need to reset our counter, and write out the count we've accumulated
for line in sys.stdin:
   line = line.strip()
   key, value = line.split("\t")

   # we have to be able to deal with missing values
   if value =="NA":
       continue
   
   value = float(value)

   # if this is the first iteration
   if not last_key:
       last_key = key
       min_value = min(min_value, value)
       max_value = max(max_value, value)
       count = 1
       sum = value

    # if they're the same, log it
   elif key == last_key:
        min_value = min(min_value, value)
        max_value = max(max_value, value)
        count = count + 1
        sum = sum + value
        
   else: 
        min_value = min(min_value, value)
        max_value = max(max_value, value)
        average_value = sum / count
        print(f"{last_key}\t{min_value}\t{max_value}\t{average_value}")

        last_key = key
        count = 1
        sum = value
        min_value = float('inf')
        max_value = float('-inf')
        

# this is to catch the final value that we output
min_value = min(min_value, value)
max_value = max(max_value, value)
average_value = sum / count
print(f"{last_key}\t{min_value}\t{max_value}\t{average_value}")

# Print the average for the last day
if last_key is not None:
    min_value = min(min_value, value)
    max_value = max(max_value, value)
    average_value = sum / count
    print(f"{last_key}\t{min_value}\t{max_value}\t{average_value}")
  
