Symbol Class
============

.. py:class:: Symbol(symbol, name, *, param_count=0, after_loop=False, action=None)

Purpose
-------

``Symbol`` stores operator metadata and the callable behavior associated with a
symbol.

Key methods
-----------

``as_operator()``
   Convert the symbol metadata into an :class:`Operator`.

``compare(other)``
   Compare against another symbol or comparable value.
