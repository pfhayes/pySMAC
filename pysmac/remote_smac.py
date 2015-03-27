import types
import sys
import os
import traceback
import socket
import subprocess
from pkg_resources import resource_filename
from math import ceil

import logging
import multiprocessing

import time
import utils.limit_resources


SMAC_VERSION = "smac-v2.08.00-master-731"


# takes a name and a tuple defining one parameter, registers that with the parser
# and returns the corresponding string for the SMAC pcs file and the type of the
# variable for later casting
def process_single_parameter_definition(name, specification):
	# if this is the first parameter, set up the argument parser for SMACs output
	
	string = '%s '%name

	assert isinstance(specification, (list,tuple)), "The specification \"%s\" is not valid"%(specification,)
	assert len(specification)>1, "The specification \"%s\" is too short"%(specification,)
	dtype=types.StringType

	# numerical values
	if isinstance(specification[0], (list, tuple)):
		
		dtype=types.FloatType
		ao = set(specification[2:])
		tmp_string=''
		
		if 'int' in ao:
			tmp_string +='i'
			ao.remove('int')
			dtype=types.IntType
		if 'log' in ao:
			tmp_string +='l'
			ao.remove('log')
		assert len(ao) == 0, "unknown option(s) %s"%(list(ao), )

		string += '[ %s, %s] [%s] '%(str(dtype(specification[0][0])), str(dtype(specification[0][1])), str(dtype(specification[1]))) + tmp_string
	#categorical values
	elif isinstance(specification[0], set):
		string += '{'+ ','.join(map(str,specification[0])) +'} [%s]'%specification[1]
	else:
		raise ValueError("Sorry, I don't understand the parameter specification: %s\n"%(specification,))

	return string, dtype


# takes the users parameter definition and converts into lines for the pcs file
# and also creates a dictionary for parsing smacs output
def process_parameter_definitions(parameter_dict):
	pcs_strings = []
	parser_dict={}
	
	for k,v in parameter_dict.items():
		line, dtype = process_single_parameter_definition(k,v)
		parser_dict[k] = dtype
		pcs_strings.append(line)
		
	return (pcs_strings, parser_dict)



# function that gathers all information to build the java class path
def smac_classpath():
	logger = multiprocessing.get_logger()
	
	smac_folder = resource_filename("pysmac", 'smac/%s' % SMAC_VERSION)
	# hack for development :)
	# smac_folder = './%s/'%SMAC_VERSION
	
	smac_conf_folder = os.path.join(smac_folder, "conf")
	smac_patches_folder = os.path.join(smac_folder, "patches")
	smac_lib_folder = os.path.join(smac_folder, "lib")


	classpath = [fname for fname in os.listdir(smac_lib_folder) if fname.endswith(".jar")]
	classpath = [os.path.join(smac_lib_folder, fname) for fname in classpath]
	classpath = [os.path.abspath(fname) for fname in classpath]
	classpath.append(os.path.abspath(smac_conf_folder))
	classpath.append(os.path.abspath(smac_patches_folder))

	logger.debug("SMAC classpath: %s", ":".join(classpath))

	return classpath





class remote_smac(object):
	udp_timeout=1
	
	# Starts SMAC in IPC mode. SMAC will wait for udp messages to be sent.
	def __init__(self, scenario_fn, seed, class_path, memory_limit, parser_dict):
		self.__parser = parser_dict
		self.__subprocess = None
		self.__logger = multiprocessing.get_logger()
		
		# establish a socket
		self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.__sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.__sock.settimeout(3)
		self.__sock.bind(('', 0))
		self.__sock.listen(1)
		
		self.__port = self.__sock.getsockname()[1]
		self.__logger.debug('picked port %i'%self.__port)

		# build the java command
		cmds  = ["java"]
		if memory_limit is not None:
			cmds += ["-Xmx%im"%memory_limit]
		cmds +=	["-cp",
				":".join(class_path),
				"ca.ubc.cs.beta.smac.executors.SMACExecutor",
				"--scenario-file", scenario_fn,
				"--tae", "IPC",
				"--ipc-mechanism", "TCP",
				"--ipc-remote-port", str(self.__port),
				"--seed", str(seed)
				]
		
		self.__logger.debug("Starting SMAC in ICP mode")
		
		# connect the output to the logger if the appropriate level has been set
		if self.__logger.level < logging.WARNING:
			self.__subprocess = subprocess.Popen(cmds, stdout =sys.stdout, stderr = sys.stderr)
		else:
			with open(os.devnull, "w") as fnull:
				self.__subprocess = subprocess.Popen(cmds, stdout = fnull, stderr = fnull)

	def __del__(self):
		# shut the subprocess down on 'destruction'
		if not (self.__subprocess is None):
			self.__subprocess.poll()
			if self.__subprocess.returncode == None:
				self.__subprocess.kill()
				self.__logger.debug('SMAC had to be terminated')
			else:	
				self.__logger.debug('SMAC terminated with returncode %i', self.__subprocess.returncode)


	def next_configuration(self):
		
		while True:
			try:
				self.__logger.debug('trying to retrieve the next configuration from SMAC')
				self.__sock.settimeout(self.udp_timeout)
				self.__conn, addr = self.__sock.accept()
				fconn = self.__conn.makefile('r') 
				config_str = fconn.readline()
				break
			except socket.timeout:
				# if smac already terminated, there is nothing else to do
				if self.__subprocess.poll() is not None:
					self.__logger.debug("SMAC subprocess is no longer alive!")
					return None	
				#otherwise there is funny business going on!
				else:
					self.__logger.debug("SMAC has not responded yet, but is still alive. Will keep waiting!")

		self.__logger.debug("SMAC message: %s"%config_str)
		
		los = config_str.replace('\'','').split() # name is shorthand for 'list of strings'
		config_dict={}

				
		config_dict['instance']      = int(los[0][3:])
		config_dict['instance_info'] = str(los[1])
		config_dict['cutoff_time']   = float(los[2])
		config_dict['cutoff_length'] = float(los[3])
		config_dict['seed']          = int(los[4])

		
		for i in range(5, len(los), 2):
			config_dict[ los[i][1:] ] = self.__parser[ los[i][1:] ]( los[i+1])
		
		self.__logger.debug("Our interpretation: %s"%config_dict)
		return (config_dict)
	
	def report_result(self, value, runtime, status = 'TIMEOUT'):
		# value is only None, if the function call was unsuccessful
		if value is None:
			string = 'Result for ParamILS: %s, %f, 0, 0, 0'%(status,runtime)
		# for fancy stuff, the function can return a dict with 'status' and 'quality' keys
		elif isinstance(value, dict):
			string = 'Result for ParamILS: %s, %f, 0, %s, 0'%(value['status'],runtime, value['quality'])
		# in all other cases, it should be a float
		else:
			string = 'Result for ParamILS: SAT, %f, 0, %s, 0'%(runtime, str(value))
		self.__conn.sendall(string)
		self.__conn.close();



def remote_smac_function(only_arg):
	
	try:
	
		scenario_file, seed, function, parser_dict, memory_limit_smac_mb, class_path, num_instances, mem_limit_function, t_limit_function, deterministic = only_arg
	
		logger = multiprocessing.get_logger()
	
		smac = remote_smac(scenario_file, seed, class_path, memory_limit_smac_mb,parser_dict)
	
		logger.debug('Started SMAC subprocess')
	
		num_iterations = 0
	
		while True:
			config_dict = smac.next_configuration()

			# method next_configuration checks whether smac is still alive
			# if it is None, it means that SMAC has finished (for whatever reason)
			if config_dict is None:
				break
			
			# delete the unused variables from the dict
			if num_instances is None:
				del config_dict['instance']
			
			del config_dict['instance_info']
			del config_dict['cutoff_length']
			if deterministic:
				del config_dict['seed']
		
			current_t_limit = int(ceil(config_dict.pop('cutoff_time')))
		
			#logger.debug('SMAC suggest the following configuration:\n%s'%(config_dict,))

			# execute the function and measure the time it takes to evaluate
			wrapped_function = utils.limit_resources.enforce_limits(mem_in_mb=mem_limit_function, time_in_s=current_t_limit, grace_period_in_s = 1)(function)
			start = time.time()
			res = wrapped_function(**config_dict)
			runtime = time.time()-start
			logger.debug('iteration %i:function value %s, computed in %s seconds'%(num_iterations, str(res), str(runtime)))
			print res, runtime, current_t_limit
			if runtime < current_t_limit:
				smac.report_result(res, runtime, 'CRASHED')
			else:
				smac.report_result(res, runtime)
			num_iterations += 1
	except:
		traceback.print_exc()
