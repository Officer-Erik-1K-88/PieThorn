Equation Symbols
================

Module: :mod:`piethorn.math.equation.symbols`

Overview
--------

This module defines symbol metadata, grouped symbol collections, and operator
behavior.

.. toctree::
   :maxdepth: 1

   symbols/symbol_class
   symbols/symbols_class
   symbols/operator_class

``Symbol``
----------

.. py:class:: Symbol(symbol, name, *, param_count=0, after_loop=False, action=None)

   Metadata wrapper for parser symbols.

   Methods:

   * ``as_operator()``
   * ``compare(other)``

``Symbols``
-----------

.. py:class:: Symbols(symbols)

   Collection wrapper around multiple :class:`Symbol` objects.

   Methods:

   * ``at(index)``
   * ``contains_any(values)``
   * ``get(key, default=None)``
   * ``index(value, start=0, stop=None)``
   * ``items()``
   * ``iter(param_count=None, after_loop=True, during_loop=True)``
   * ``keys()``
   * ``values()``

``Operator``
------------

.. py:class:: Operator(operator)

   Behavior-bearing symbol wrapper used during evaluation.

   Methods:

   * ``calculate(num1, num2)``
   * ``compare(num1, num2)``
   * ``union(*args)``

Grouped symbol collections
--------------------------

``COMPARISON_SYMBOLS``
   Comparison operators.

``MATH_SYMBOLS``
   Arithmetic operators.

``UNION_SYMBOLS``
   Boolean-union operators.

Autodoc
-------

.. automodule:: piethorn.math.equation.symbols
   :members:
   :undoc-members:
