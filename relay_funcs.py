import json
import sys
import os
import os.path



OFFSET_CYCLE_READ = 2 # offset zero base index and refer to next cycle
READS_TO_CONSIDER = 40 # Help speeds things up by only looking at this many reads




def zero_fail(my_json):
    suite_fails = my_json["test-suite-fail-count"]
    return suite_fails == 0

def more_then_zero(my_json):
  suite_fails = my_json["test-suite-fail-count"]
  return suite_fails > 0

def check_all(my_json):
  return True

def get_test_suite_from_files(file_names):
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

  return None


def find_gate_open(case):
  analytics = case["analytics"]
  max_gate_open = 0
  previous_write = 0

  # Only Checking from off to closed. Looking for last closed position
  for entry in analytics:
    slot_id = entry["slot-id"]
    write_val = entry["write"] # value written for 4 channels
    if type(write_val) == str:
      write_val = int(write_val,16)
      
    channel_reads = entry["din"]["reads"][1::2]

    for which_channel, channel_vals in enumerate(channel_reads):
      open_cycle = 0
      if not (which_channel == 3 and (previous_write & 8) and (write_val & 8)):
        consecutive_zero_read = 0
        for index, open in enumerate(channel_vals):
          if open == 0:
            consecutive_zero_read += 1
            if consecutive_zero_read == 10:
              if open_cycle > max_gate_open:
                max_gate_open = open_cycle              
              break
          else:
            consecutive_zero_read = 0
            open_cycle = index + OFFSET_CYCLE_READ

    previous_write = write_val


  # print(max_gate_open)
  return max_gate_open


# finds max closer time for whole case
def find_gate_close_max(case):
  analytics = case["analytics"]
  max = 0

  # Only Checking from off to closed. Looking for last closed position
  for entry in analytics:
    write_val = entry["write"] # value written for 4 channels

    if type(write_val) == str:
      write_val = int(write_val, 16)
      
    
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


  # print(f"Max Gate Closer: ", max)
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

    
def shaun_csv(case, cpu_temp):
  # print("****")
  # go through each case and append to csv file
  # cols: temp, slot, channel, state, time
  # cols: temp, [1,4], {3,6,9,12}, {open, close}, <millisecond max time>

  #open file for read_backs
  #open and closes for each channel
  # with open("force_guided_relay4_din.csv") as out:
  din_file_name = "din_open_close.csv"
  rb_file_name = "read_back_open_close.csv"
  header = "cpu_temp,slot,channel,state,ms\n"
  if not os.path.isfile(din_file_name):
    with open(din_file_name, 'w') as append_header:
      append_header.write(header)

  if not os.path.isfile(rb_file_name):
    with open(rb_file_name,'w') as append_header:
      append_header.write(header)

  ######################################################### DIN OPEN
  with open(din_file_name,"a+") as din_file:
    analytics = case["analytics"]
    max_gate_open_per_channel = 0
    slot_id = case["slot-id"]
    ############################# OPEN
    for entry in analytics:
      
      write_val = entry["write"] # value written for 4 channels
      if type(write_val) == str:
        write_val = int(write_val,16)
        
      # Reads transition from 1 to zero. Others are dropped when if not greater then zero
      channel_reads = entry["din"]["reads"][1::2]
      for which_channel, channel_vals in enumerate(channel_reads):
        open_cycle = 0
        max_gate_open_per_channel = 0

        consecutive_zero_read = 0
        for index, is_open in enumerate(channel_vals):
          if is_open == 0:
            consecutive_zero_read += 1
            if consecutive_zero_read == 10:
              if open_cycle > max_gate_open_per_channel:
                max_gate_open_per_channel = open_cycle              
              break
          else:
            consecutive_zero_read = 0
            open_cycle = index + OFFSET_CYCLE_READ

        if max_gate_open_per_channel > 0:
          din_file.write(f"{cpu_temp},{slot_id},{which_channel},open,{max_gate_open_per_channel}\n")
          # print(cpu_temp, slot_id, which_channel, "open", max_gate_open_per_channel)

      # Cycle channel reads again for close time
      ########################### CLOSE
      if write_val > 0:# Nothing to measure if write is zero
        max = 0
        was_channel_written = [write_val & 1, write_val & 2, write_val & 4, write_val & 8] # help find which channel was written to
        for channel_index, was_written in enumerate(was_channel_written):
          if was_written > 0: # this channel was written to
            channel_under_test_reads = channel_reads[channel_index] 

            for index_by_millisecond in range(READS_TO_CONSIDER):
              if channel_under_test_reads[index_by_millisecond] == 0: #Look for last time channel relay was open to consider bounce
                max = index_by_millisecond + OFFSET_CYCLE_READ
            max += 1 # find last time gate is open next one is closed
            din_file.write(f"{cpu_temp},{slot_id},{channel_index},close,{max}\n")
########################################################## DIN OPEN END

  ######################################################### READBACK OPEN
  with open(rb_file_name,"a+") as rd_file:
    

    analytics = case["analytics"]
    slot_id = case['slot-id']

    max_gate_open = 0
    
    # Only Checking from off to closed. Looking for last closed position
    for entry in analytics:
      channel_reads = entry["read_back"]["reads"]
      write_val = entry["write"] # value written for 4 channels

      # print("type", type(channel_reads))
      ################ OPEN
      for which_channel, channel_vals in enumerate(channel_reads):
        open_cycle = 0
        max_gate_open = 0
        
        consecutive_zero_read = 0
        for index, is_open in enumerate(channel_vals):
          if is_open == 0:
            consecutive_zero_read += 1
            if consecutive_zero_read == 10:
              if open_cycle > max_gate_open:
                max_gate_open = open_cycle              
              break
          else:
            consecutive_zero_read = 0
            open_cycle = index + OFFSET_CYCLE_READ

        if max_gate_open > 0:
          rd_file.write(f"{cpu_temp},{slot_id},{which_channel},open,{max_gate_open}\n")
          # print(f"{cpu_temp},{slot_id},{which_channel},open,{max_gate_open}")


      ################# CLOSE
      max = 0
      if write_val > 0:
        channels = [write_val & 1, write_val & 2, write_val & 4, write_val & 8] # help find which channel was written to
        for index, channel in enumerate(channels):
          if channel > 0: # this channel was written to
            
            channel_reads = entry["read_back"]["reads"]
            channel_under_test_reads = channel_reads[index] 
            for i in range(READS_TO_CONSIDER):
              if channel_under_test_reads[i] == 0: #Look for last time channel relay was open to consider bounce
                max = i + OFFSET_CYCLE_READ # offset 0 base index and then next cycle
            rd_file.write(f"{cpu_temp},{slot_id},{index},close,{max}\n")
            # print(f"{cpu_temp},{slot_id},{index},close,{max}")
######################################################### READBACK OPEN END



  
def find_gate_open_read_back(case):

  analytics = case["analytics"]
  slot_id = case['slot-id']

  max_gate_open = 0
  previous_write = 0
  # Only Checking from off to closed. Looking for last closed position
  for entry in analytics:
    channel_reads = entry["read_back"]["reads"]
    write_val = entry["write"] # value written for 4 channels
    for which_channel, channel_vals in enumerate(channel_reads):
      open_cycle = 0
      if not (which_channel == 3 and (previous_write & 8)and (write_val & 8)):
        consecutive_zero_read = 0
        for index, open in enumerate(channel_vals):
          if open == 0:
            consecutive_zero_read += 1
            if consecutive_zero_read == 10:
              if open_cycle > max_gate_open:
                max_gate_open = open_cycle              
              break
          else:
            consecutive_zero_read = 0
            open_cycle = index + OFFSET_CYCLE_READ

    previous_write = write_val


  print(max_gate_open)
  return max_gate_open



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
