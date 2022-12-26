import json
import sys
import os

OFFSET_CYCLE_READ = 2 # offset zero base index and refer to next cycle
READS_TO_CONSIDER = 40 # Help speeds things up by only looking at this many reads

def find_gate_close_max_read_back(case):
  analytics = case["analytics"]
  max = 0

  i = 0
  # Only Checking from off to closed. Looking for last closed position
  for entry in analytics:
    write_val = entry["write"] # value written for 4 channels
    
    if write_val > 0:
      channels = [write_val & 1, write_val & 2, write_val & 4, write_val & 8] # help find which channel was written to
      for index, channel in enumerate(channels):
        if channel > 0: # this channel was written to
          
          channel_reads = entry["read_back"]["reads"]
          channel_under_test_reads = channel_reads[index] 
          for i in range(READS_TO_CONSIDER):
            if channel_under_test_reads[i] == 0: #Look for last time channel relay was open to consider bounce
              max = i + OFFSET_CYCLE_READ # offset 0 base index and then next cycle

  # print(f"Max Gate Closer: ", max)
  return max



def get_test_suite_from_files(file_names, restriction = None):
  for file in file_names:
    with open(file) as log_file:

      for json_entry in log_file:
        is_error = json_entry.find("[error]")
        if is_error != -1:
          print("*Error: ", json_entry)
          
        arr = json_entry.split("[info]")
        log_entry = arr[0]
        my_json = None
        try:
          my_json = json.loads(arr[1])    
          yield my_json
        except Exception as ex:
      
          print(f"error reading line: Exception: {ex}")

  return -1




def find_gate_close_max(case):
  analytics = case["analytics"]
  max = 0

  # Only Checking from off to closed. Looking for last closed position
  for entry in analytics:
    write_val = entry["write"] # value written for 4 channels
    
    if write_val > 0:
      channels = [write_val & 1, write_val & 2, write_val & 4, write_val & 8] # help find which channel was written to
      for index, channel in enumerate(channels):
        if channel > 0: # this channel was written to
          channel_reads = entry["din"]["reads"][1::2]
          channel_under_test_reads = channel_reads[index] 

          for i in range(READS_TO_CONSIDER):
            if channel_under_test_reads[i] == 0: #Look for last time channel relay was open to consider bounce
              max = i + OFFSET_CYCLE_READ
          max += 1 # find last time gate is open next one is closed


  print(f"Max Gate Closer: ", max)
  return max

def find_unsafe_wiring_fault(case):
  print("***START UNSAFE")
  analytics = case["analytics"]

  
  # Only Checking from off to closed. Looking for last closed position
  for entry in analytics:
    
    write_val_str = entry["write"] # value written for 4 channels
    write_val = int(write_val_str,16)
    # print(f"write value str: {write_val_str} actual: {write_val}")
    # return 0
    # pass
    read_backs = entry["read_back"]["reads"]
          
    which_channels_are_high_with_write_val = []
    for channel_index in range(len(read_backs)):
      which_channels_are_high_with_write_val.append((1 if (write_val & (1 << channel_index)) else 0))

    # print(which_channels_are_high_with_write_val)

    for channel_index, rb_channels_arr in enumerate(read_backs):
      val_for_channel = which_channels_are_high_with_write_val[channel_index]
      for rb_index, rb in enumerate(rb_channels_arr):
        if rb_index > 3 and val_for_channel != rb:
          print(f"fail on channel: {channel_index} with read: {rb_index}    expected: {val_for_channel}   got: {rb}")

    



