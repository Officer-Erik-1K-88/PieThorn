Equation Tokens
===============

Module: :mod:`pythorn.math.equation.tokens`

.. toctree::
   :maxdepth: 1

   tokens/equation_piece
   tokens/number_token
   tokens/variable_token

``EquationPiece``
-----------------

.. py:class:: EquationPiece(value)

   Generic token wrapper with parent tracking.

   Main members:

   * ``value``
   * ``parent``
   * ``has_parent()``

``Number``
----------

.. py:class:: Number(number)

   Parsed decimal literal token.

``Variable``
------------

.. py:class:: Variable(name, default=None)

   Parsed variable token.

   Methods:

   ``has_default()``
      Return whether the variable includes a default value.

Autodoc
-------

.. automodule:: pythorn.math.equation.tokens
   :members:
   :undoc-members:
