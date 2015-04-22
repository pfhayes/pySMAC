import json
import functools
import re
import operator

import numpy as np


# taken from 
# http://stackoverflow.com/questions/21708192/how-do-i-use-the-json-module-to-read-in-one-json-object-at-a-time/21709058#21709058
def json_parse(fileobj, decoder=json.JSONDecoder(), buffersize=2048):
	buffer = ''
	for chunk in iter(functools.partial(fileobj.read, buffersize), ''):
		buffer += chunk
		buffer = buffer.strip(' \n')
		while buffer:
			try:
				result, index = decoder.raw_decode(buffer)
				yield result
				buffer = buffer[index:]
			except ValueError:
				# Not enough data to decode, read more
				break


# Reads a run_results file from a state-run folder and stores in a numpy array
# The run results are the only non numeric column here. They are mapped
# according to:
# SAT -----> 1
# UNSAT ---> 0
# TIMEOUT -> -1
# ELSE ----> -2
def read_runs_and_results_file(fn):
	# to convert everything into floats, the run result needs to be mapped
	def map_run_result(res):
		if b'SAT' in res:    return(1)
		if b'UNSAT' in res:    return(0)
		if b'TIMEOUT' in res:return(-1) 
		return(-2)    # covers ABORT, CRASHED, but that shouldn't happen
	
	return(np.loadtxt(fn, skiprows=1, delimiter=',',
		usecols = list(range(1,14))+[15], # skip empty 'algorithm run data' column
		converters={13:map_run_result}))


# reads a paramstring file from a state-run folder
# The returned list contains dictionaries with
# 'parameter_name': 'value_as_string' pairs
def read_paramstrings_file(fn):
	param_dict_list = []
	with open(fn,'r') as fh:
		for line in fh.readlines():
			# remove run id and single quotes
			line = line[line.find(':')+1:].replace("'","")
			pairs = map(lambda s: s.strip().split("="), line.split(','))
			param_dict_list.append({k:v for [k, v] in pairs})
	return(param_dict_list)

 
# Reads a validationCallString file and returns a list of dictonaries
# Each dictionary consists of parameter_name: value_as_string entries
def read_validationCallStrings_file(fn):
	param_dict_list = []
	with open(fn,'r') as fh:
		for line in fh.readlines()[1:]: # skip header line
			config_string = line.split(",")[1].strip('"')
			config_string = config_string.split(' ')
			tmp_dict = {}
			for i in range(0,len(config_string),2):
				tmp_dict[config_string[i].lstrip('-')] = config_string[i+1].strip("'")
			param_dict_list.append(tmp_dict)
	return(param_dict_list)


def read_validationObjectiveMatrix_file(fn):
	values = {}
	
	with open(fn,'r') as fh:
		header = fh.readline().split(",")
		num_configs = len(header)-2
		re_string = '\w?,\w?'.join(['"id\_(\d*)"', '"(\d*)"']  + ['"([0-9.]*)"']*num_configs)
		for line in fh.readlines():
			match = (re.match(re_string, line))
			values[int(match.group(1))] = map(float,map(match.group, range(3,3+num_configs)))
	return(values)


def read_instances_file(fn):
    with open(fn,'r') as fh:
        instance_names = fh.readlines()
    return(map(lambda s: s.strip(), instance_names))


def read_instance_features_file(fn):
    instances = {}
    with open(fn,'r') as fh:
       for line in  fh.readline():
           tmp = line.strip().split(" ")
           instances[tmp[0]] = None if len(tmp) == 1 else " ".join(tmp[1:])
    return(map(lambda s: s.strip(), instance_names))




if __name__ == "__main__":
	#print(read_paramstrings_file(   '/home/sfalkner/repositories/bitbucket/pysmac2/spysmac_on_minisat/out/scenario/state-run2/paramstrings-it126.txt'))
	#print(read_run_and_results_file('/home/sfalkner/repositories/bitbucket/pysmac2/spysmac_on_minisat/out/scenario/state-run2/runs_and_results-it126.csv'))
	#print(read_validationCallString_file('/home/sfalkner/repositories/bitbucket/pysmac2/spysmac_on_minisat/out/scenario/validationCallStrings-traj-run-1-walltime.csv'))
	print(read_validationObjectiveMatrix_file('/home/sfalkner/repositories/bitbucket/pysmac2/spysmac_on_minisat/out/scenario/validationObjectiveMatrix-traj-run-1-walltime.csv'))
