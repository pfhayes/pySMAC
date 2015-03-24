pysmac
======

Simple python wrapper to [SMAC](http://www.cs.ubc.ca/labs/beta/Projects/SMAC/), a versatile tool for optimizing algorithm parameters.

SMAC is free for academic & non-commercial usage. Please contact Frank Hutter to discuss obtaining a license for commercial purposes.

This wrapper is intented to use SMAC directly from Python to minimize a objective function. It also contains some rudimentary analyzing tools that can also be applied to already existing SMAC runs.



Installation
------------

To install pysmac, we advise using the Python package management system:

```

pip install git+https://github.com/sfalkner/pysmac.git --user

```

If you prefer, you can clone the repository and install it manually via

```

python setup.py install

```


Basic Usage
-----------

One main focus of this project is to offer a very simple interface to novice users that want to use SMAC within python. On the other hand,
we also strive to provide more advanced users access to (almost) all parameters and advanced functionality that SMAC has to offer. A very simple example could be

```python

import pysmac

def sum_of_squares(x1, x2):
	return(x1**2 + x2**2)

opt = pysmac.SMAC_optimizer()

parameter_definition=dict(\
		x1=( [-5, 5],  1),			# this line means x1 is a float between -5 and 5, inital guess is 1
		x2=( [-5, 5], -1),	# same as x1, but the initial value is -1
		)

value, parameters = opt.minimize(sum_of_squares		# the function to be minimized
					, 100							# the maximum number of function evaluations
					, parameter_definition)			# the parameter dictionary

print('The minimum value %f was found for the configurations %s'%(value, parameters))

```

It highlights the four steps involved in using pySMAC:

1. Define the function that you want to minimize. In this case it is "sum_of_squares"
2. Create an SMAC_optimizer object.
3. Provide a description of the parameters your function takes.
4. Call the minimize method of the SMAC_optimizer object to start SMAC on your problem.

Note that the result of this optimization will not be impressive. SMACs is meant for
problems that have many parameters which can be continuous, integral or categorical.
It can also handle dependencies and contstraints between parameters, as often found in
the context of algorithm configuration. For smooth functions, other approaches will
work better.

The documentation of this package consists (for now) of example scripts that show various
aspects of pySMACs abilities.
