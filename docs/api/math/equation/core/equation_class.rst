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
   from piethorn.math.equation import Equation

   equation = Equation("$value$ + $fallback:2$", Context())
   equation.calculate({"value": 3})

Methods
-------

``has_variables()``
   Return whether the parsed equation contains variables.

   .. code-block:: python

      Equation("1 + 2", Context()).has_variables()
      Equation("$value$ + 2", Context()).has_variables()

``calculate(variables=None)``
   Evaluate the expression with optional variable values.

   .. code-block:: python

      Equation("1 + 2 * 3", Context()).calculate()
      Equation("$value$ + 1", Context()).calculate({"value": 4})

Behavior notes
--------------

Equations without variables cache their computed value after the first
evaluation.

Variables use decimal conversion through :class:`decimal.Decimal`, and missing
required variables raise ``ValueError``.
