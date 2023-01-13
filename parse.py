import json
import sys
import os

import relay_funcs as relay
import matplotlib.pyplot as plt 
import numpy as np



def test_suites(files, conditions = None, funcs = None):
  max_gate_closer = 0
  temp_map = {}
  processed_count = 0

  for my_json in relay.get_test_suite_from_files(files):
    # print(my_json)
    # continue
    #do something with conditions
    skip_file = False

    for con in conditions:
      if not con(my_json):
        skip_file = True 
    
    if skip_file:
      continue

    processed_count += 1

    suite_fails = my_json["test-suite-fail-count"]    
    cpu_temp = my_json["diagnostics"]["cm_cpu_temp"]
    # print("CPU TEMP: ", cpu_temp , "Fail count: ", suite_fails)

    #functions
    for entry in my_json["test_suites"]:
      for case in entry["test_cases"]:
        slot = case["slot-id"]
        for func in funcs:
          if func == relay.find_gate_close_max :
            func_return = func(case)
            if func_return > max_gate_closer:
              max_gate_closer = func_return
              
            if cpu_temp in temp_map:
              temp_map[cpu_temp].append(func_return)
            else:
              temp_map[cpu_temp] = [func_return]
          
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
          elif func == relay.find_gate_open_read_back or func == relay.find_gate_open:
            func_return = func(case)
            if func_return > max_gate_closer:
              max_gate_closer = func_return
              
            if cpu_temp in temp_map:
              temp_map[cpu_temp].append(func_return)
            else:
              temp_map[cpu_temp] = [func_return]
          elif func == relay.shaun_csv:
            func(case,cpu_temp)
          
          

  print(f"Total Processed: {processed_count}")
  print(f"Max Gate Closer: {max_gate_closer}")

  if relay.find_gate_close_max_read_back in funcs or relay.find_gate_close_max in funcs or relay.find_gate_open_read_back in funcs or relay.find_gate_open in funcs:
  # if False:
    x = []
    average = []
    mins = []
    maxes = []
    variance = []
    for key in temp_map:
      x.append(key)
      average.append(sum(temp_map[key])/len(temp_map[key]))
      mins.append(min(temp_map[key]))
      maxes.append(max(temp_map[key]))

      var = np.var(temp_map[key])
      variance.append(var)

    slope, intercept = np.polyfit(x,average,deg=1)

    x = np.array(x)
    average= np.array(average)
    mins = np.array(mins)
    variance = np.array(variance)
    x = np.array(x)
    plt.errorbar(x, average, variance, fmt='ok', lw=3)
    plt.errorbar(x, average, [average - mins, maxes - average],
             fmt='.k', ecolor='gray', lw=1)
    # plt.ylim(10,30)
    print("Early Exit from Plotting")
    return
    plt.show()

    return
    fig, ax = plt.subplots()
    ax.scatter(x,average)
    ax.bar(x,variance)
    line_thing = np.linspace(min(x),max(x), len(x))
    ax.plot(line_thing,  intercept + slope * line_thing,color='r')
    
    fig.legend(["Points",f"Slope: {slope:.2f}"])
    ax.set_title("Average Max_gate temperature")
    plt.show()



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

  
  # funcs = [relay.find_unsafe_wiring_fault]
  # funcs = [relay.find_gate_close_max]
  # funcs = [relay.find_gate_close_max_read_back]
  # funcs = [relay.find_gate_open_read_back]
  funcs = [relay.shaun_csv]

  # print(files)
  # exit()
  # process_files(files)
  # test_suites(files, [relay.check_all], funcs)
  if funcs[0] == relay.shaun_csv:
    os.system("rm din_open_close.csv")
    os.system("rm read_back_open_close.csv")
  test_suites(files, [relay.zero_fail], funcs)


