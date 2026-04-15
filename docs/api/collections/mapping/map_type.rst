Map Type
========

.. py:class:: Map(keys=None, values=None, *, loop_fill=False)

Purpose
-------

``Map`` is an ordered mutable mapping with explicit key-index and value-index
operations.

Construction constraints
------------------------

* ``keys`` and ``values`` must both be provided or both be omitted
* they must have identical length

Examples
--------

.. code-block:: python

   from pythorn.collections.mapping import Map

   mapping = Map(["a", "b"], [1, 2])
   mapping["a"] = 3
   mapping["c"] = 4

Important methods
-----------------

``has_key(key)`` / ``has_value(value)``
   Membership tests.

``key_index(key)`` / ``value_index(value)``
   Return insertion positions.

``key_at_index(index)`` / ``value_at_index(index)``
   Indexed retrieval helpers.
