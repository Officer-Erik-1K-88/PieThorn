FuncParam Class
===============

.. py:class:: FuncParam(name, takes_boolean, required, default=None, value=None)

Purpose
-------

``FuncParam`` is the parsed representation of a function argument during
equation parsing.

Behavior
--------

It combines equation-parameter semantics with parsed-equation tree behavior so
that nested expressions can exist inside one function argument.
