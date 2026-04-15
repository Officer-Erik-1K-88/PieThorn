Parameter Class
===============

.. py:class:: Parameter(name, takes_boolean=False, default=None, value=None, required=False)

Purpose
-------

``Parameter`` represents one declared equation function parameter.

Key concepts
------------

``takes_boolean``
   Marks the parameter as expecting a boolean expression.

``default`` / ``value`` / ``required``
   Define fallback behavior and whether a missing value is allowed.

Inherited helpers
-----------------

``get()``, ``is_empty()``, ``new(value)``
