Operator Class
==============

.. py:class:: Operator(operator)

Purpose
-------

``Operator`` is the behavior-bearing token used during evaluation.

Key methods
-----------

``calculate(num1, num2)``
   Apply the operator as arithmetic.

   .. code-block:: python

      from decimal import Decimal
      from pythorn.math.equation import Operator

      Operator("+").calculate(Decimal("1"), Decimal("2"))

``compare(num1, num2)``
   Apply the operator as comparison.

   .. code-block:: python

      Operator("<").compare(Decimal("1"), Decimal("2"))

``union(*args)``
   Apply the operator as boolean union logic.

   .. code-block:: python

      Operator("&").union(True, False)

Behavior notes
--------------

``calculate`` only accepts operators registered in ``MATH_SYMBOLS``.
``compare`` only accepts operators registered in ``COMPARISON_SYMBOLS``.
