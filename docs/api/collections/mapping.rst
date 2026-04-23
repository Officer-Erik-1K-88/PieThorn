Mapping Module
==============

Module: :mod:`piethorn.collections.mapping`

Overview
--------

This module provides:

* :class:`Pair`, a small immutable key/value holder
* :class:`Map`, an ordered mutable mapping implemented with parallel key and
  value lists

.. toctree::
   :maxdepth: 1

   mapping/map_type

``Pair``
--------

.. py:class:: Pair(key, value)

   Frozen dataclass used when a lightweight key/value pair object is needed.

``Map``
-------

.. py:class:: Map(keys=None, values=None, *, loop_fill=False)

   Dictionary-like container that preserves insertion order and exposes
   list-style index helpers.

   Construction rules
   ~~~~~~~~~~~~~~~~~~

   * ``keys`` and ``values`` must either both be ``None`` or both be sequences
   * the sequences must have the same length
   * when ``loop_fill=False``, mutable sequences may be stored directly

   Example
   ~~~~~~~

   .. code-block:: python

      from piethorn.collections.mapping import Map

      mapping = Map(["a", "b"], [1, 2])
      mapping["a"] = 3
      mapping["c"] = 4

   Key methods
   ~~~~~~~~~~~

   ``has_key(key)``
      Return whether the key exists.

   ``has_value(value)``
      Return whether an equal value exists.

   ``key_index(key, start=0, stop=sys.maxsize)``
      Return the insertion index of a key.

   ``value_index(value, start=0, stop=sys.maxsize)``
      Return the insertion index of a value.

   ``key_at_index(index)``
      Return the key stored at an insertion index.

   ``value_at_index(index)``
      Return the value stored at an insertion index.

   Example sequence of calls
   ~~~~~~~~~~~~~~~~~~~~~~~~~

   .. code-block:: python

      mapping.key_index("c")     # 2
      mapping.value_index(2)     # 1
      mapping.key_at_index(0)    # "a"
      mapping.value_at_index(2)  # 4
      list(mapping)              # ["a", "b", "c"]
      list(reversed(mapping))    # ["c", "b", "a"]

Autodoc
-------

.. automodule:: piethorn.collections.mapping
   :members:
   :undoc-members:
