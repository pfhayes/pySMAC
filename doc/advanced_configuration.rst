================================
Advanced configuration of pySMAC
================================

Restricting your Functions Resources
------------------------------------

Often in algorithm configuration (SMAC's main application), some configurations
may take too long, consume more memory than they should or have other undesired
sideeffects. To guard agains these cases, pySMAC utilizes a Python module called
**pynisher** which allows you to specify certain limits for your function.
Specifically, you can limit your functions memory consumption, cpu time,
and wall clock time. Refer to the :py:meth:`pysmac.optimizer.SMAC_optimizer.minimize`
documentation for further details. Similar limits can be applied to the SMAC process(es)
started in the background. Please see :py:meth:`pysmac.optimizer.SMAC_optimizer` for more.

If your function takes too long, or tries to allocate too much memory,
the subrocess encapsulating your function receives a signal, and is aborted.
Please refere to the pynisher manual for more details.


.. _advanced_options:

Additional (py)SMAC Options
---------------------------

The API of pySMAC is designed to allow a low barrier entry into using it,
but SMAC is a very powerful tool that comes with numerous features. For a
novice this complexity might be overwhelming, but more experienced users
need to be able to access the full potential of SMAC. This is the reason
why pySMAC forces you to create a SMAC_optimizer object and call its
member function minimize. In principle, this could be combined into a
simple function. But splitting it up into two steps allows to modify
the standard options of SMAC itself and some advanced features of pySMAC.

The large number of options in SMAC is far too large to implement a proper
python function taking those as arguments without cluttering the interface
and/or running into trouble when new options are added in future versions.
Instead, the *SMAC_optimizer* object has an attribute called **smac_options**.
This is a dict where the keys-value pair represent a SMAC option and the
corresponding value. It is populated with some defauld values
on creation of the *SMAC_optimizer* object, and will be used to start SMAC
inside the *minimize* method. That way, the user has full control over
every SMAC option by manipulating the entries of said dict before starting
the minimization.

For example, you might want to change the number of trees in the random 
forest SMAC fits internally to the observed data. You would look into the
SMAC manual to find this option is called "--rf-num-trees" for calling
SMAC from the command line. To use this option in pySMAC, add the key
"rf-num-trees" (dropping the leading hyphens) like that:

.. code-block:: python
    
    opt = pysmac.SMAC_optimizer()
    opt.smac_options['rf-num-trees'] = 16

Now, SMAC would fit 16 trees when the minimize method is called.

There are a few entries in this dictionary that are not SMAC, but pySMAC
options:

    +----------------+------------------------------------------------------------+---------------+
    | Name           | Description                                                | Default       |
    +================+============================================================+===============+
    |scenario_fn     | All important SMAC options are stored in a scenario file.  | 'scenario.dat'|
    |                | This option sets the name for that file.                   |               |
    +----------------+------------------------------------------------------------+---------------+
    |java_executable | SMAC itself runs inside a Java Runtime Environment. This   | 'java'        |
    |                | option controlls how Java is invoced on the command line.  |               |
    |                | It is possible to pass additional arguments to java using  |               |
    |                | this entry. E.g., '/usr/bin/java -d32' would tell pySMAC   |               |
    |                | where the java binary can be found and that it should use  |               |
    |                | a 32-bit data model if available. Use this if the system   |               |
    |                | wide command java is not the JRE you want pySMAC to use.   |               |
    +----------------+------------------------------------------------------------+---------------+

Optimizing Runtime instead of Quality
-------------------------------------

Minimizing a function is a relatively general problem which, in principle,
also allows for runtime optimization. But optimizing the duration rather
than the result is so common and allows for a customized approach that
SMAC has a dedicated mode for it. One of the key differences between 
minimizing a functions return value (the quality) rather then the runtime,
is that incomplete runs still contain valuable information in the latter
case. Imaging, SMAC already encountered a configuration that can finish in
5 seconds. For subsequent runs, there is no need to wait for the function
to finish for more than that. The corresponding option is called **run-obj**,
and can take the values 'RUNTIME' or 'QUALITY' (default for pySMAC).

If you want to optimize runtime, the return value of your function should not
be the duration you want SMAC to record for this call. pySMAC automatically
measures the CPU time of your function. The actual return value of your 
function is somewhat irrelevant. However, if you want to overwrite pySMAC's
time measurement, your function can return a ``dict`` where the following keys
are used:

    +-------------+--------------------------------------------------------+
    |    Key      |  Explanation                                           |
    +=============+========================================================+
    | value       | The actual function value. Should be a float.          |
    +-------------+--------------------------------------------------------+
    | runtime     | The time that is recorded for this run. Does have      |
    |             | to be the actual runtime, but your function will       |
    |             | contraint to CPU time if you optimize run time.        |
    |             | Use this to provide a more precise time measurement.   |
    +-------------+--------------------------------------------------------+
    | status      | SMAC has historically strong ties to the SAT community,|
    |             | and where every run yields either shows that a given   |
    |             | boolean formula is satisfiable or unsatisfialble.      |
    |             | The status indicates whether the run was succesfull    |
    |             | (SAT/UNSAT) or not (TIMEOUT/CRASHED/ABORT). Please     |
    |             | consult the SMAC manual for more details.              |
    +-------------+--------------------------------------------------------+



.. _training_instances:

Optimizing on a Set of Instances
--------------------------------

Commonly in algorithm configuration, one is not only interested in optimizing
the a simple function, but rather the overall performance across a set of
instances (sometimes called the training set). This adds to the complexity
of the problem as a single configuration has to be evaluated on several 
instances to estimate its performance. 

The num_train_instances argument of :py:meth:`pysmac.optimizer.SMAC_optimizer.minimize`
specifies the number of instances your function accepts. If it is a positive
integer, pySMAC will call your function with an additional argument, called **instance**.
This parameter will be an int in ``range(num_train_instances)``. What the
underlying meaning of this instance number is has to be implemented in your
function. For example, one can use different cross-validation folds as
instances when optimizing a machine learning method. The file
*sklearn_example_advanced_crossvalidation.py* shows this usecase.



.. _validation:

Validation
----------

When optimizing on instances, the final evaluation of a configurations
performance does not take place on the training set used during the 
optimization. This usually leads to overfitting, and poor generalization
to unseen instances. Instead, a separate set, called the test set, is used
to assess the performance of a configuration.

This behavior is activated in pySMAC by specifying the argument
num_test_instances of :py:meth:`pysmac.optimizer.SMAC_optimizer.minimize`.
These instances are represented by integers from ``range(num_train_instances, num_train_instances + num_test_instances)``.

After the budget of function evaluations is exausted, SMAC will run
the configuration with the best estimated trainings performance on the 
complete test set as a validation.

.. note::

    Right now, this option overwrites the entries 
    ``validate-only-last-incumbent`` and ``validation`` in the smac_option
    dict (see :ref:`advanced_options`) with ``True``. In future versions,
    pySMAC should/will honor user set values for those variables.


.. _non-deterministic:

Non-determinstic Functions
--------------------------

If your function uses any source of randomness, and its performance might
crucially depend on it, SMAC can take this into account. In order get
reproducible results, SMAC now also associates a seed with every call, that
becomes an argument of your function. Given the same seed and the same input
you function be deterministic. This way, SMAC can rerun the same configuration
with different seeds to estimate the performance. By setting 
``deterministic = False`` in the call to :py:meth:`pysmac.optimizer.SMAC_optimizer.minimize`
this behavior is enabled.

