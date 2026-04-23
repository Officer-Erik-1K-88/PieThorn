Equation Parameters
===================

Module: :mod:`piethorn.math.equation.parameters`

.. toctree::
   :maxdepth: 1

   parameters/parameter_class
   parameters/parameters_class

``Param``
---------

.. py:class:: Param()

   Abstract interface for equation parameters.

   Methods
   ~~~~~~~

   ``get()``
      Return the effective value, falling back to the default.

   ``is_empty()``
      Return whether both value and default are empty.

   ``new(value)``
      Return a new parameter with the same definition and a new bound value.

``Parameter``
-------------

.. py:class:: Parameter(name, takes_boolean=False, default=None, value=None, required=False)

   Concrete parameter definition with optional bound value.

   Example
   ~~~~~~~

   .. code-block:: python

      from piethorn.math.equation import Parameter

      p = Parameter("amount", default=2, value=5)
      p.get()  # 5

``Parameters``
--------------

.. py:class:: Parameters(parameters=None)

   Ordered parameter collection.

   Methods
   ~~~~~~~

   ``check(parameters)``
      Return whether another parameter set matches required filling and length.

   ``fill(parameters)``
      Copy provided values into this declared layout.

   ``required_filled()``
      Return whether every required parameter now has a value.

   ``get_named_parameter(name)``
      Return a named parameter or raise ``KeyError``.

Autodoc
-------

.. automodule:: piethorn.math.equation.parameters
   :members:
   :undoc-members:
