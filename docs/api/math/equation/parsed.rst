Parsed Equation Structures
==========================

Module: :mod:`pythorn.math.equation.parsed`

Overview
--------

These classes represent the mutable token tree produced during parsing.

.. toctree::
   :maxdepth: 1

   parsed/parsed_equation
   parsed/equation_func
   parsed/func_param

``ParsedEquation``
------------------

.. py:class:: ParsedEquation(parsed_equation=None)

   Mutable sequence of parsed equation pieces with tracking for nested
   sub-expressions and function calls.

   Important properties:

   * ``var_count``
   * ``var_count_default``
   * ``in_sub``
   * ``in_function``

   Important methods:

   ``enter_sub()`` / ``exit_sub()``
      Enter or leave nested sub-expression parsing.

   ``get_sub(...)``
      Return the active child sub-expression.

   ``enter_function(name, index)`` / ``exit_function()``
      Enter or leave function-call parsing.

   ``get_function()`` / ``get_function_parent()``
      Return the active function or its owning parse node.

   ``get_current(...)``
      Return the currently active parse target.

   ``append(value)``, ``extend(values)``, ``insert(index, value)``, ``clear()``,
   ``pop(index=-1)``, ``remove(value)``
      Mutable sequence operations routed to the active parse target.

``EquationFunc``
----------------

.. py:class:: EquationFunc(index, name)

   Parsed representation of a function call inside an equation.

   Methods:

   * ``add_param(param)``
   * ``get()``
   * ``get_param()``

``FuncParam``
-------------

.. py:class:: FuncParam(name, takes_boolean, required, default=None, value=None)

   Parsed representation of one function argument.

Autodoc
-------

.. automodule:: pythorn.math.equation.parsed
   :members:
   :undoc-members:
