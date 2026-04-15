ParsedEquation Class
====================

.. py:class:: ParsedEquation(parsed_equation=None)

Purpose
-------

``ParsedEquation`` is the mutable parse tree used while building and traversing
equation expressions.

Important state
---------------

``var_count``, ``var_count_default``, ``in_sub``, ``in_function``

Key methods
-----------

``enter_sub()``, ``exit_sub()``, ``get_sub(...)``
   Manage nested sub-expressions.

``enter_function(...)``, ``exit_function()``, ``get_function()``,
``get_function_parent()``
   Manage nested function-call parsing.

``get_current(...)``
   Return the active insertion target.
