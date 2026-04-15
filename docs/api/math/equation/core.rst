Equation Core
=============

Module: :mod:`pythorn.math.equation.core`

``Equation``
------------

.. py:class:: Equation(equation, context)

   Parse an equation string into a reusable evaluation object.

   Example
   ~~~~~~~

   .. code-block:: python

      from decimal import Context
      from pythorn.math.equation import Equation

      eq = Equation("$value$ + $fallback:2$", Context())
      eq.calculate({"value": 3})  # Decimal("5")

   Properties
   ~~~~~~~~~~

   ``equation``
      Original equation string.

   ``context``
      Decimal context used for evaluation.

   Methods
   ~~~~~~~

   ``has_variables()``
      Return whether the parsed equation references variables.

   ``calculate(variables=None)``
      Evaluate the parsed equation. Missing required variables raise
      ``ValueError``.

.. toctree::
   :maxdepth: 1

   core/equation_class

Autodoc
-------

.. automodule:: pythorn.math.equation.core
   :members:
   :undoc-members:
