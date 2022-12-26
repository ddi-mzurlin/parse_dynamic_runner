import json
import sys
import os

import relay_funcs as relay
import matplotlib.pyplot as plt 



def test_suites(files, conditions = None, funcs = None):
  max_gate_closer = 0
  temp_map = {}
  temperature = []
  gate_close = []


  for my_json in relay.get_test_suite_from_files(files):
    #do something with conditions
    skip_file = False

    for con in conditions:
      if not con(my_json):
        skip_file = True 
    
    if skip_file:
      continue


    suite_fails = my_json["test-suite-fail-count"]    
    cpu_temp = my_json["diagnostics"]["cm_cpu_temp"]
    print("CPU TEMP: ", cpu_temp , "Fail count: ", suite_fails)

    #functions
    for entry in my_json["test_suites"]:
      for case in entry["test_cases"]:
        slot = case["slot-id"]
        for func in funcs:
          if func == relay.find_gate_close_max :
            func_return = func(case)
            if func_return > max_gate_closer:
              max_gate_closer = func_return
          elif func == relay.find_unsafe_wiring_fault:
            if slot == 6:
              func(case)
          elif func == relay.find_gate_close_max_read_back:
            func_return = func(case)
            if func_return > max_gate_closer:
              max_gate_closer = func_return
              
            if cpu_temp in temp_map:
              temp_map[cpu_temp].append(func_return)
            else:
              temp_map[cpu_temp] = [func_return]

        

  if relay.find_gate_close_max_read_back in funcs:
    x = []
    y = []
    for key in temp_map:
      x.append(key)
      y.append(sum(temp_map[key])/len(temp_map[key]))

    plt.scatter(x,y)
    plt.xlabel("Temp C")
    plt.ylabel("Average gate closer in miliseconds")
    plt.show()

  # print("Global Max Gate Closer time: ", max_gate_closer)
  # print("Total Test-Suite fails: ", max_suite_fail_count)
    




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
  # print(f"files: {files}")

  # funcs = []
  # funcs = [relay.find_gate_close_max]
  # funcs = [relay.find_unsafe_wiring_fault]
  funcs = [relay.find_gate_close_max_read_back]

  # process_files(files)
  test_suites(files, [relay.zero_fail], funcs)






# def process_files(files, funcs = None):
#   global max_gate_closer
#   global temp_max_on_read_back

#   show_at_fail_count = 1
#   max_suite_fail_count = 0
#   suite_fails = 0
#   previous_fail_count = 0
#   # output = open("temp_and_max_gate_closer", 'w')

#   temp_map = {}
#   temperature = []
#   gate_close = []

#   for file in files:
#     with open(file) as log_file:

#       for line in log_file:
#         test = line.find("[error]")
#         if test != -1:
#           print("*Error: ", line)
          
#         arr = line.split("[info]")
#         log_entry = arr[0]

#         try:
#           my_json = json.loads(arr[1])    
          
#           suite_fails = my_json["test-suite-fail-count"]

#           # if True:
#           if suite_fails  > 0:
#           # if suite_fails  > 0 and suite_fails != previous_fail_count:
#             previous_fail_count = suite_fails
#             cpu_temp = my_json["diagnostics"]["cm_cpu_temp"]
#             print(log_entry, "CPU TEMP: ", cpu_temp , "Fail count: ", suite_fails)

#             for entry in my_json["test_suites"]:
#               for case in entry["test_cases"]:
#                 slot = case["slot-id"]
          
#           if suite_fails > max_suite_fail_count:
#             max_suite_fail_count = suite_fails
            
#         except Exception as ex:
      
#           print(f"error reading line: Exception: {ex}")
#       # output.close()                      

#   if relay.find_gate_close_max_read_back in funcs:
#     x = []
#     y = []
#     for key in temp_map:
#       x.append(key)
#       y.append(sum(temp_map[key])/len(temp_map[key]))
#       # y.append(max(temp_map[key]))
#       # sum = 0
#       # entries = 0
#       # for vals in temp_map[key]:
#         # sum += vals

#     # plt.plot(x,y)
#     plt.scatter(x,y)
#     plt.xlabel("Temp C")
#     plt.ylabel("Average gate closer in miliseconds")
#     # plt.ylim([5,12])
#     plt.show()

#   print("Global Max Gate Closer time: ", max_gate_closer)
#   print("Total Test-Suite fails: ", max_suite_fail_count)
    

