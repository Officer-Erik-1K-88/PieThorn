Equation Class
==============

.. py:class:: Equation(equation, context)

Purpose
-------

``Equation`` parses an expression once and exposes repeatable decimal-based
evaluation.

Example
-------

.. code-block:: python

   from decimal import Context
   from pythorn.math.equation import Equation

   equation = Equation("$value$ + $fallback:2$", Context())
   equation.calculate({"value": 3})

Methods
-------

``has_variables()``
   Return whether the parsed equation contains variables.

``calculate(variables=None)``
   Evaluate the expression with optional variable values.
