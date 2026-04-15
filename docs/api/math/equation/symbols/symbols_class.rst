Symbols Class
=============

.. py:class:: Symbols(symbols)

Purpose
-------

``Symbols`` is an ordered mapping from symbol text to :class:`Symbol` objects.

Key methods
-----------

``at(index)``, ``get(key, default=None)``, ``index(value, start=0, stop=None)``
   Lookup helpers.

``contains_any(values)``
   Membership helper for groups of values.

``iter(param_count=None, after_loop=True, during_loop=True)``
   Filtered symbol iteration helper.
