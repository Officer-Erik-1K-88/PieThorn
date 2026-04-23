Equation Functions
==================

Module: :mod:`piethorn.math.equation.functions`

.. toctree::
   :maxdepth: 1

   functions/function_class
   functions/functions_registry

``Function``
------------

.. py:class:: Function(name, value=None, parameters=None, action=None)

   Represents a callable or constant value usable inside equations.

   Modes
   ~~~~~

   * constant-value functions such as ``pi``
   * action-based functions with declared parameter definitions

   Example
   ~~~~~~~

   .. code-block:: python

      from piethorn.math.equation import Function, Parameter, Parameters

      func = Function(
          "sum",
          parameters=Parameters((
              Parameter("left", required=True),
              Parameter("right", required=True),
          )),
          action=lambda params: params[0].get() + params[1].get(),
      )

   Methods
   ~~~~~~~

   ``is_value()``
      Return whether this is a constant-value function.

   ``apply(param_handler=None)``
      Evaluate the function via a parameter handler or return the constant
      value.

   ``__call__(parameters)``
      Evaluate the action-based function with filled parameters.

``Functions``
-------------

.. py:class:: Functions(*functions)

   Ordered mutable registry of :class:`Function` objects.

   Methods
   ~~~~~~~

   ``append(function)``, ``insert(index, function)``, ``extend(functions)``
      Add functions to the registry.

   ``get(name)``
      Retrieve a function by name.

   ``name_index(name, start=0, stop=None)``
      Return the position of a function name.

   ``names()``
      Return all registered names as a tuple.

``FUNCTIONS``
-------------

Default registry containing the built-in equation constants and helpers.

Autodoc
-------

.. automodule:: piethorn.math.equation.functions
   :members:
   :undoc-members:
