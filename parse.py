import json
import sys
import os

import relay_funcs as relay

max_gate_closer = 0

def process_files(files, funcs = None):
  global max_gate_closer

  show_at_fail_count = 1
  max_suite_fail_count = 0
  suite_fails = 0
  previous_fail_count = 0


  for file in files:
    with open(file) as log_file:

      for line in log_file:
        test = line.find("[error]")
        if test != -1:
          print("*Error: ", line)
          
        arr = line.split("[info]")
        start = arr[0]

        try:
          my_json = json.loads(arr[1])    
          
          suite_fails = my_json["test-suite-fail-count"]

          if True:
          # if suite_fails  > 0 and suite_fails != previous_fail_count:
            previous_fail_count = suite_fails
            cpu_temp = my_json["diagnostics"]["cm_cpu_temp"]
            print(start, "CPU TEMP: ", cpu_temp , "Fail count: ", suite_fails)

            for entry in my_json["test_suites"]:
              for case in entry["test_cases"]:
                slot = case["slot-id"]
                                
                for func in funcs:
                  if func == relay.find_gate_close_max :
                    temp = func(case)
                    if temp > max_gate_closer:
                      max_gate_closer = temp
                  elif func == relay.find_unsafe_wiring_fault:
                    if slot == 6:
                      func(case)
                  elif func == relay.find_gate_close_max_read_back:
                    temp = func(case)
                    if temp > max_gate_closer:
                      max_gate_closer = temp
                    print(cpu_temp, temp)
                  
              
          
          if suite_fails > max_suite_fail_count:
            max_suite_fail_count = suite_fails
            
        except Exception as ex:
          print(f"error reading line: Exception: {ex}")
    print("Global Max Gate Closer time: ", max_gate_closer)
    print("Total Test-Suite fails: ", max_suite_fail_count)
    



if __name__ == "__main__":
  if len(sys.argv) <= 1:
    print("Require file name. Terminating")
    quit()
    
  errors = {}
  with open("errors.json") as error_open:
    errors = json.load(error_open)


  file = sys.argv[1]
  key = ""
  if len(sys.argv) == 3:
    key = sys.argv[2]



  files = [] 

  if os.path.isdir(file):
    if file[-1] != '/':
      file += "/"
    for i in os.listdir(file): 
      newDir = file + i + "/"
      newDir = newDir.replace('"', '\"')
      if os.path.isdir(newDir):
        for j in os.listdir(newDir): 
          newFile = newDir + j
          files.append(newDir + j)
        
      else:
        files.append(file + i)

  else:
    files.append(file)
  print(f"files: {files}")

  # funcs = []
  # funcs = [relay.find_gate_close_max]
  # funcs = [relay.find_unsafe_wiring_fault]
  funcs = [relay.find_gate_close_max_read_back]

  # process_files(files)
  process_files(files, funcs)