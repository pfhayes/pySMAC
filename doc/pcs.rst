.. _pcs:

==========================================
Defining the Parameter Configuration Space
==========================================

This pages explains in detail how the types, allowed and default
values of all parameters are defined. It also covers how dependencies
and constraints between them can be modeled.

.. _parameter_defs:

Parameter Definitions
=====================

The definition of the parameters is stored in a dictionary, where the name
of the parameter as the key, and a tuple containing all necessary information
constitutes the corresponding value. SMAC, the configuration system underlying
pySMAC, discriminates four different parameter types:

1. **real** -- take any value in a specified range.
2. **integer** -- take any integral value in a specified range.
3. **categorical** -- take one of a finite set of values.
4. **ordinal** -- are essentially categorical parameters with a natural ordering between the elements.


We shall look at a simple example for all four types to show how they are defined:

.. code-block:: python

	parameter_definitions=dict(\
	a_float_parameter =       ("real"       , [-3.5, 2.48]                             , 1.1           ),
	an_integer_parameter =    ("integer"    , [1, 1000]                                ,  2      ,"log"),
	a_categorical_parameter = ("categorical", ["yes", "no", "maybe"]                   , "yes"         ),
	a_ordinal_parameter =     ("ordinal"    , ["cold", "cool", "medium", "warm", "hot"], "medium"      )
	)

The definition of each parameter follows the same pattern: first its type,
followed by a list defining the allowed values, and finally the default value.

For **real** and **integer** type, the allowed values are defined by a range,
represented by a list with exactly two elements. The default
value has to be inside this range to yield a legal definition. Both the
range and the default of an **integer** have to be Python **int**\s

There exists an optional flag "log" that can be given additionally as the
last element of a tuple for these two types. If given, the parameter is
varied on a logarithmic scale, meaning that the logarithm of the value is
uniformly distributed between the logarithm of the bounds. Therefore, this
option can only be given if the parameter is strictly positive!

For **categorical** and **ordinal** the list of allowed values can contain 
any number (>0) of elements. Every element constitutes a valid value for
this parameter. The default value has to be among them. The ordering of
an **ordinal** parameter is established by the order in the list.

The Python type for **categorical** and **ordinal** parameters can be a numeric
type of a string. The only restriction is, that all allowed values for one 
parameter are all of the same time. For example, the following definition is
not valid:

.. code-block:: python

	parameter_definitions=dict(\
	        a = ("integer"    , [1, 1000] ,  2.0 ),       # default value is not of type int
        	b = ("categorical", ["True", "False",1], 1),  # 2 str and one int value
	)


.. note::

    Defining the parameter configuration space can be quite challenging, e.g.,
    if the number of parameters is large. So typos and/or inconsistencies
    can happen. SMAC itself checks the definitions in great detail, and pySMAC
    provides also some sanity checks with (hopefully) helpful error messages
    to assist in this tedious task. 




Conditional Parameter Clauses
=============================

In many cases, certain parameters only have any meaning if another one takes
a certain value. For example, one parameter might activate or deactivate  a
subroutine which has parameters itself. Naturally, the latter are only relevant
when the subroutine is actually used. These dependencies can be expressed in
pySMAC to accelerate the configuration process (by reducing the number of
active parameters).

To illustrate this, let's focus on the example in ``sklearn_model_selection.py``.
The script demonstrates a use-case from machine learning. Given a data set, there
are numerous models that can be used to *learn* from it and apply this *knowledge*
to unseen data points. In this simple example, we generate a random data set and
try to find the model (with the best parameter settings) among only three very basic
ones, namely: k-nearest-neighbors, random forests, and extremely randomized trees.
In order to run that example, you need the scikit-learn package, but the
source code below should be illustrative enough to show how to use conditionals.


.. literalinclude:: ../examples/sklearn_model_selection.py
    :linenos:


The output looks like that (note the random data set leads to slightly different numbers for every run):

.. code-block:: shell

    The default accuracy of the random forest is 0.909091
    The default accuracy of the extremely randomized trees is 0.903030
    The default accuracy of k-nearest-neighbors is 0.863636
    The highest accuracy found: 0.936364
    Parameter setting {'knn_weights': 'distance', 'trees_n_estimators': '8', 'knn_n_neighbors': '1', 'classifier': 'random_forest', 'trees_max_features': '10', 'trees_max_depth': '2', 'trees_criterion': 'gini'}

The script shows how pySMAC can be used for model selection and simultaneous
optimization. The function to be minimized (*choose_classifier*, line 19)
returns the negative accuracy of training one out of three machine learning
models (a random forest, extremely randomized trees, and k-nearest-neighbors).
So effectively, SMAC is asked to maximize the accuracy choosing either of
these models and its respective parameters.

The parameter definitions are stated between line 44 and 55. Naturally,
the ones for K-nearest-neighbors and the two tree based classifiers are
independent. Therefore, the parameters of the former
affect the accuracy only if this classifier is actually chosen.

The variable *conditionals*, defined in line 64, shows some examples for 
how these dependencies between parameters are expressed. Generally they
follow the template:

.. code-block:: shell

    child_name | condition1 (&& or ||) condition2 (&& or ||) ...

The *child* variable is only considered active if the logic expression following 
the "|" is true.

.. note:: 

    From the SMAC manual
	* Parameters not listed as a child in any conditional parameter clause are always active.
	* A child's name can appear only once.
	* There is no support for parenthesis with conditionals. The && connective has higher precedence than ||, so a||b&& c||d is the same as a||(b&&c)||d. 

The conditions can take different forms:

.. code-block:: c

    parent_name in {value1, value2, ... }
    parent_name == value                      parent_name != value
    parent_name <  value                      parent_name >  value

The first one is true if the parent takes any of the values listed. The 
other expressions have the regular meaning. The operators in the last line
are only legal for **real**,  **integer** or **ordinal**, while the
others can be used with any type.


Forbidden Parameter Clauses
=============================

In some use-cases, certain parameter configurations might be illegal, or
lead to undefined behavior. For example, some algorithms might be able to
employ different data structures, and different subroutines, controlled
by two parameters:

.. code-block:: python

    parameter_definition = dict(\
	    DS = ("categorical", [DataStructure1, DataStructure2, DataStructure3],DataStructure1 ),
	    SR = ("categorical", [SubRoutine1, SubRoutine2, SubRoutine3], SubRoutine1)
    )


Let's assume that DataStructure2 is incompatible with SubRoutine3,
i.e. evaluating this combination does not yield a meaningful result,
or might even cause a system crash. That means one out of nine possible
choices for these two parameters is forbidden.
 
One can certainly change the parameters and their definitions such that they exclude
this case explicitly. One could, i.e., combine the two parameters and list
all eight allowed values:

.. code-block:: python

    parameter_definition = dict(\
	    DS_SR =  ("categorical", [DS1_SR1, DS1_SR2, DS1_SR2, DS2_SR1, DS2_SR2, DS3_SR1, DS3_SR2, DS3_SR3], [DS1_SR1])
    )

This is not only unpractical, but it forbids SMAC to learn about the data
structures and subroutines independently. It is much more efficient to
specifically exclude this one combination by defining a forbidden parameter
clause. The **classic syntax** is as follows:

.. code-block:: python

    "{parameter_name1 = value1, ..., parameter_nameN = ValueN}"
    
It allows to specify combinations of values that are forbidden. For our
example above, the appropriate forbidden clause would be

.. code-block:: python

    forbidden_confs = ["{DS = DataStructure2, SR = SubRoutine3}"]

.. note::
    The pair of curly braces {} around the expression is mandatory. The
    pySMAC notation here is a direct copy of the SMAC one. These strings
    are merely handed over to SMAC without any processing. That way, 
    statements from the SMAC manual are applicable to pySMAC as well.

A list of all forbidden clauses is than passed to the minimize method 
with the forbidden_clauses keyword. So the corresponding
call to the minimize method would look like this:

.. code-block:: python

    opt = pySMAC.SMAC_optimizer()
    value, config = opt.minimize(function_to_minimize, num_function_calls,
				 parameter_definition,
				 forbidden_clasuses = forbidden_confs)


Of course, conditionals and forbidden clauses are not mutual exclusive, 
but you can define both and use them while minimizing the function.

Introduced in SMAC 2.10, there is an **advanced syntax** that allows more
complex situations to be handled. It allows to compare parameter values to
each other, and apply a limit set of functions:

    +---------------------+----------------------------------------------------------------------------------------+
    |Arithmetic Operations| +,-,*,/,^, Unary +/-, and %                                                            |
    +---------------------+----------------------------------------------------------------------------------------+
    |    Functions        | abs, (a)cos, (a)sin, (a)tan, exp, sinh, cosh, ceil, floor, log, log2, log10, sqrt, cbrt|
    +---------------------+----------------------------------------------------------------------------------------+
    |  Logical Operators  | >=, <=, >, <, ==, !=, ||, &&                                                           |
    +---------------------+----------------------------------------------------------------------------------------+


Some examples (without the appropriate parameter definitions) to illustrate this notation:

.. code-block:: python

        forbidden_confs = ["{activity == 'swimming' && water_temperature < 15}",
                           "{x^2 + y^2  < 1}",
                           "{sqrt(a) + log10(b) >= - exp(2)}"]





.. note::
    The SMAC manual has an extensive section on important tips and caveats
    related to forbidden parameters. Here are some major points
    
	* SMAC generates random configurations without honoring the forbidden clauses, but rejects those that violate at least one. So constraining the space too much will slow down the process.
	* Even meaningless forbidden clauses (those that are always false) still take time to evaluate slowing SMAC down.
	* Applying arithmetic operations/function to non-numerical values for categoricals/ordinals leads to undefined behavior!
	  For **categorical** types only == and != should be used. You may use >=, <=, <, and > for **ordinal** parameters.
	* Don't use == and != for **real** types, as they are almost always false, or true respectively.
	* names and values of parameters must not contain anything besides alphanumeric characters and underscores.
	* When defining **ordinal** parameters, you have to keep the values consistent. E.g.
	
	  .. code-block:: python
	    
	    parameter_definition = dict(\
		a = ("ordinal", ["warm", "medium", "cold"], "medium"),
		b = ("ordinal", ["cold", "medium", "warm"], "medium"),
		c = ("ordinal", [100, 10, 1], 100))

	  The problem here is that "warm < cold" for a, but "warm > cold" for b.
	  For numerical values the definition of c implies "100<10", which is not true.
    
    For more details, please refer to the SMAC manual.
