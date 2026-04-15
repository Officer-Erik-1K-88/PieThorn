EvalParser Class
================

.. py:class:: EvalParser(chars, context)

Purpose
-------

``EvalParser`` streams over character input and produces a
``ParsedEquation`` tree.

Key methods
-----------

``parse()``
   Parse the full expression.

``peek()``, ``eat(char)``, ``next()``
   Consume or inspect input characters.

``has_current()``, ``has_next()``, ``next_ended()``, ``char_count()``
   Query parser input state.
