import json

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




def read_run_and_results_file(fn):
	
	# to convert everything into floats, the run result needs to be mapped
	def map_run_result(res):
		if 'SAT' in res:	return(1)
		if 'UNSAT' in res:	return(0)
		if 'TIMEOUT' in res:return(-1) 
		return(-2)	# covers ABORT, CRASHED, but that shouldn't happen
	
	return(np.loadtxt(fn, skiprows=1, delimiter=',',
		usecols = range(1,14)+[15], # skip empty 'algorithm run data' column
		converters={13:map_run_result}))


def read_paramstrings_file(fn):
	param_dict_list=[];
	with open(fn) as fh:
		for line in fh.readlines():
			
			# remove run id and single quotes
			line = line[line.find(':')+1:].replace("'","")
			pairs = map(lambda s: s.strip().split("=") , line.split(','))
			
			param_dict_list.append({k:v for [k,v] in pairs})
	return(param_dict_list)
			


if __name__ == "__main__":
	print read_paramstrings_file('/home/sfalkner/bitbucket/pysmac2/spysmac_on_minisat/out/scenario/state-run1/paramstrings-it430.txt')
	bla = read_run_and_results_file('/home/sfalkner/bitbucket/pysmac2/spysmac_on_minisat/out/scenario/state-run2/runs_and_results-it205.csv')
	
	import matplotlib.pyplot as plt
	
	plt.hist(bla[:,6])
	plt.show()

