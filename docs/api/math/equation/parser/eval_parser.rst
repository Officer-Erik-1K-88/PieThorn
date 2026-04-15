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

   .. code-block:: python

      parser.parse()

``peek()``, ``eat(char)``, ``next()``
   Consume or inspect input characters.

   .. code-block:: python

      parser.peek()

``has_current()``, ``has_next()``, ``next_ended()``, ``char_count()``
   Query parser input state.

Behavior notes
--------------

``EvalParser`` sits on top of the character-iteration helpers, so its cursor and
lookahead behavior follow the same stream-style parsing semantics as
``CharIterator``.
