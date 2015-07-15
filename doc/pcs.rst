==========================================
Defining the Parameter Configuration Space
==========================================

This pages explains in detail how the types, allowed values, and default
values of all parameteers are defined. It also covers how dependencies
and constraints between them are expressed.


Parameter Definitions
=====================


The definition of the parameters is stored in a dictionary, where the name
of the parameter as the key, and a tuple containing all information. SMAC,
the configuration system underlying pySMAC, descriminates four different parameter types:

1. **real** -- take any value in a specified range.
2. **integer** -- take any integral value in a specified range.
3. **categorical** -- take one of a finite set of values.
4. **ordinal** -- are essentially categorical parameters with a natural ordering between the elements.


We shall look at a simple example for all four times to show how they are defined:

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
represented by a list with exactly two (numerical) elements. The default
value has to be inside this range to yield a legal definition.

There exists an optional flag "log" that can be given additionally as the
last element of a tuple for these two types. If given, the parameter is
varied on a logarithmic scale, meaning that the logarithm of the value is
uniformly distributed between the logarithm of the bounds. Therefor, this
option can only be given if the parameter is strictly positive! In the 
above example **

For **categorical** and **ordinal** the list of allowed values can contain 
any number (>0) of elements. Every element constitutes a valid value for
this parameter. The default value has to be among them. The ordering of
an ordinal parameter is established by the order in the list.

A sidenode
----------

Defining the parameter configuration space can be quite challenging, e.g.,
if the number of parameters is large, so typos and resulting inconsistencies
can happen. SMAC itself checks the definitions in great detail, and pySMAC
provides also some sanity checks with (hopefully) helpful error messages
to help with this tedious task. 



