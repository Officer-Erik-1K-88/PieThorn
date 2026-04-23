Equation Parser
===============

Module: :mod:`piethorn.math.equation.parser`

``EvalParser``
--------------

.. py:class:: EvalParser(chars, context)

   Streaming parser used by :class:`piethorn.math.equation.core.Equation`.

   Example
   ~~~~~~~

   .. code-block:: python

      from decimal import Context
      from piethorn.collections.char import CharSequence
      from piethorn.math.equation import EvalParser

      parser = EvalParser(CharSequence("1 + 2"), Context())
      parser.parse()
      parser.parsed

   Methods
   ~~~~~~~

   ``parse()``
      Parse the full input.

   ``peek()``, ``eat(char)``, ``next()``
      Character-stream helpers inherited from the parser's iterator behavior.

   ``has_current()``, ``has_next()``, ``next_ended()``, ``char_count()``
      Input-state helpers.

   ``for_remaining(action)``
      Iterate the remaining characters through a callback.

.. toctree::
   :maxdepth: 1

   parser/eval_parser

Autodoc
-------

.. automodule:: piethorn.math.equation.parser
   :members:
   :undoc-members:
