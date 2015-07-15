================
Quickstart Guide
================

This quickstart guide tries to show the basic mechanisms of how to use pySMAC
to find good input parameters to a python function to minimize the return value. 

To gain familiarity with the workflow, we shall disect the file "branin_example.py"
which can be found in the example folder. The full script looks like this:

.. code-block:: python

    import pysmac
    import math

    def modified_branin(x1, x2, x3):
	if (int(x3) != x3):
	    raise ValueError("parameter x3 has to be an integer!")
	if (x3<0):
	    raise ValueError("parameter x3 has to be positive!")

	a = 1
	b = 5.1 / (4*math.pi**2)
	c = 5 / math.pi
	r = 6
	s = 10
	t = 1 / (8*math.pi)
	ret  = a*(x2-b*x1**2+c*x1-r)**2+s*(1-t)*math.cos(x1)+s + x3
	return ret

    parameter_definition=dict(\
		x1=('real',    [-5, 5],  1),
		x2=('real',    [-5, 5], -1),
		x3=('integer', [0, 10],  1)
		)

    opt = pysmac.SMAC_optimizer()
    value, parameters = opt.minimize(modified_branin, 1000, parameter_definition)

    print('Lowest function value found: {}'.format(value))
    print('Parameter setting {}'.format(parameters))


After the necessary imports, the function '''modified_branin''' is defined.
The standard Branin function is well know and often used test function in the
Baysian Optimization community. Here, we added a third paramater, x3, purely for
demonsting a case usually not handled by standard optimizers. We want it to be
a non-negative integer and just add it to the original function value.

The next step is to specify the type, range and default value of every 
parameter in a way pySMAC understands. Here, this is done by defining 
the dictionary

.. code-block:: python

    parameter_definition=dict(\
		x1=('real',    [-5, 5],  1),
		x2=('real',    [-5, 5], -1),
		x3=('integer', [0, 10],  1)
		)

Every entry defines an entry with the parameter name as the key and a tuple
as the corresponding value. The first entry of the tuple defines the type, 
here x1 and x2 are '''real''', i.e. continuous parameters while x3 is an integer.
The second entry defines the possible value. For numerical parameters, this has 
to be a 2-element list containing the smallest and the largest allowed value.
The third tuple entry is the default value. This has to be inside the specified
range.

This example only shows real and integer parameters without any constraints.
Please refere to the section *Defining the Parameter Configuration Space* for
a complete reference.

To start the actual minimization, we instantiate a SMAC_optimizer object,
and call its minimize method with at least 3 argument:

.. code-block:: python

    opt = pysmac.SMAC_optimizer()
    value, parameters = opt.minimize(modified_branin, 1000, parameter_definition)

The arguments of minimze are the function we which to minimize, the budged
of function calls, and the parameter definition. It returns the lowest 
function value encountered, and the corresponding parameter configuration
as a dictionary with parameter name - parameter value as key-value pairs.

The reason why an object is created before a minimization function is called
will become clear in the section *Advanced configuration of pySMAC*

As already mentioned above, the found function value is not competative
to other optimizers on the *standard Branin function* which can
exploit the coninuity of x1 and x2, but cannot be applied out of the box
to our modified version. The output of running the example here reads:

.. code-block:: html

    Lowest function value found: 0.521565
    Parameter setting {'x3': 0, 'x2': 2.3447806193471035, 'x1': 3.280718422274644}

The true minimium is at (3.1415926, 2.275, 0) with a function value of 0.397887.
But the purpose of this quickstart guide was soley to introduce how to use
pySMAC rather than showing an interesting example.
