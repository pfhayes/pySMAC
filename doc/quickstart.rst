================
Quickstart Guide
================

This quickstart guide tries to show the basic mechanisms of how to use pySMAC
to find good input parameters to a python function minimizing the return value. 

To gain familiarity with the workflow, we shall dissect the file "rosenbrock_example.py"
which can be found in the example folder. The full script looks like this:

.. literalinclude:: ../examples/rosenbrock_example.py
        :linenos:

After the necessary import, the function ''rosenbrock_4d'' is defined.
This function function is well know and often used test function in the
optimization community. Normally, all parameters are continuous, but we
will declare three of them to be integer valued to demonstrate the different
types that (py)SMAC supports.

The next step is to specify the type, range and default value of every 
parameter in the  ``pySMAC way``. In our example, this is done by defining 
the dictionary

.. code-block:: python

        parameters=dict(\
                x1=('real',       [-5, 5], 5),
                x2=('integer',    [-5, 5], 5),
                x3=('categorical',[5, 2, 0, 1, -1, -2, 4, -3, 3, -5, -4], 5), 
                x4=('ordinal',    [-5,-4,-3,-2,-1,0,1,2,3,4,5] , 5),
                )    

Every entry defines a parameter with its name as the key and a tuple
as the corresponding value. The first entry of the tuple defines the type, 
here ``x1`` is a **real**, i.e. a continuous parameter, while ``x2`` is an integer.
**Categorical** types, like ``x3``, can only take a value from a user-provided set.
There is no specific order among the elements, which is why in the example the
order of the values is shuffled. In contrast, **ordinal** parameters posses an
inherent ordering between their values. In the defining list, elements are
assumed to be in increasing order.

The second entry of the tuple defines the possible value. For numerical parameters,
this has to be a 2-element list containing the smallest and the largest allowed value.
For **categorical** and **ordinal** values this list contains all allowed values.

The third tuple entry is the default value. This has to be inside the specified
range for **real** and **integer**, or an element of the previous list for
**ordinal** and **categorical**.
Please refer to the section :ref:`parameter_defs` for more detail.

The example here is cooked up and overly complicated for the actual optimization
problem. For instance, the definitions for ``x2`` and ``x4`` are identical, and
defining ``x3`` as a **categorical** with only integral values is not exactly the
same as a **integer** type. But the purpose of this guide was to introduce pySMAC's
syntax, not solving an interesting problem in the most efficient way possible.

To start the actual minimization, we instantiate a SMAC_optimizer object,
and call its minimize method with at least 3 argument:

.. code-block:: python

    opt = pySMAC.SMAC_optimizer()
    value, parameters = opt.minimize(rosenbrock_4d, 1000, parameters)

The arguments of minimze are the function we which to minimize, the budged
of function calls, and the parameter definition. It returns the lowest 
function value encountered, and the corresponding parameter configuration
as a dictionary with parameter name - parameter value as key-value pairs.

The reason why an object is created before a minimization function is called
will become clear in the section :ref:`advanced_configuration`.

The output of the code could look like this:

.. code-block:: html

        Lowest function value found: 1.691811
        Parameter setting {'x3': '1', 'x1': '0.9327937187899629', 'x4': '1', 'x2': '1'}

with the true minimum at (1,1,1,1) having a function value of 0. Given 1000
function evaluations, this result is not competitive to continuous optimizers
if we would drop the integral restriction for ``x2``, ``x3``, and ``x4``. Continuous
optimization allows to estimate and exploit gradients which can lead to a much
faster convergence towards a local optimum. But the purpose of this quickstart guide
is solely to introduce how to use pySMAC rather than showing an interesting example.
The strength of pySMAC become more visible in more complicated cases that are usually
infeasible for standard optimizers.
