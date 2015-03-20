from __future__ import print_function

import pysmac
import math



# To demonstrate the use, we shall look at a slight modification of the well-
# known branin funtcion. To make things a little bit more interesting, we add
# a third parameter (x3). It will be an integer, which is usually not handled by
# global minimizers. 
# SMAC will acutally not impress for this function as SMACS focus is more on
# larger dimensional problems with also categorical parameters, and possible
# dependencies between them. This is where the underlying random forest realy 
# shines.

def modified_branin(x1, x2, x3):
    
    a = 1.
    b = 5.1 / (4.*math.pi**2)
    c = 5. / math.pi
    r = 6.
    s = 10.
    t = 1. / (8.*math.pi)
    ret  = a*(x2-b*x1**2+c*x1-r)**2+s*(1-t)*math.cos(x1)+s + abs(x3)
    return ret



# The definition of the parameters for the function we like to minimize.
# The representation tries to stay close to the SMAC manual, but deviates
# if necessary. # Because we use a Python dictionary to represent the
# parameters, there are different ways of creating it. The author find the 
# following way most intuitive:

parameter_definition=dict(\
		x1=( [-5, 5],  1),			# float range
		x2=( [-5, 5], -1),			# float range
		x3=( [-5, 5],  1, 'int'),	# int
		)

# Of course, the same can be achieved by

parameter_definition = { 'x1': ( [-5, 5],  1),
                         'x2': ( [-5, 5], -1),
                         'x3': ( [-5, 5],  1, 'int') }


# or, if you like it incrementally:

parameter_definition = {}
parameter_definition['x1'] = ( [-5, 5],  1)
parameter_definition['x2'] = ( [-5, 5], -1)
parameter_definition['x3'] = ( [-5, 5],  1, 'int')




def simple_example():
	# first, create a SMAC_optimizer object
	opt = pysmac.SMAC_optimizer()
	# than call its minimize function with at least the three mandatory parameters
	value, parameters = opt.minimize(modified_branin	# the function to be minimized
						, 100							# the maximum number of function evaluations
						, parameter_definition)			# the parameter dictionary
	
	print('Lowest function value found: %f'%value)
	print('Parameter setting %s'%parameters)
	




simple_example()




exit(0)
"""

#more advanced example
import time

time.sleep(1)

parameter_dict=dict(\
		x1=( [-5,5], 1),			# float range
		x2=( [-5,5], -1),			# float range
		x3=( [-5,5], 1, 'int'),						# int
		)

# additional argument for more control
opt = SMAC_optimizer(	deterministic = True,					# whether the function is deterministic
						t_limit_total_s=0, mem_limit_smac_mb=None,	# set bounds to the total time and smacs memory consumption
						debug=True,							# for debugging output
						persistent_files=True,					# SMAC output files are not deleted after completion 
						working_directory='/home/sfalkner/bitbucket/pysmac2/test2/')	# specify a folder for smacs output (default a folder provided by the tempfile module)


# full access to all smac options:
opt.smac_options['console-log-level']='INFO'
opt.smac_options['rf-num-trees'] = 20

print opt.minimize(mod_branin, 1000, parameter_dict,			# mandatory parameters
			conditional_clauses = [], forbidden_clauses=[], # add conditionsal and forbidden clauses as strings
			num_instances = 5,							# functionality of instances! Note: provided function has to 
															# accept keyword instance which will be an int in range (num_instances)
			seed = 42,  num_procs = 4, num_runs = 2,		# run multiple runs ins parallel
			mem_limit_function_mb=1000, t_limit_function_s = 2)	# restrict the resources

exit(0)
"""
