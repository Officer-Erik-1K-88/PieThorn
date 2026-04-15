Range Helpers Module
====================

Module: :mod:`pythorn.collections.range`

Overview
--------

This module focuses on composing and analyzing Python slices.

``combine_slices``
------------------

.. py:function:: combine_slices(slice1, slice2, max_len)

   Compose ``slice1`` and ``slice2`` exactly when the original sequence length
   is known.

   .. code-block:: python

      from pythorn.collections.range import combine_slices

      combine_slices(slice(2, 10, 2), slice(1, 3), 20)
      # slice(4, 8, 2)

``SliceMode``
-------------

.. py:class:: SliceMode

   Enum describing how dependent a slice is on source sequence length.

   The most important entry point is:

   ``classify(s1, s2=None)``
      Return one mode or a three-value tuple describing two slices and their
      combined mode.

``SliceComposeResult``
----------------------

.. py:class:: SliceComposeResult(slice, exact, mode)

   Dataclass used by :func:`adhoc_combine_slices`.

   Fields
   ~~~~~~

   ``slice``
      The produced best-effort or exact slice.

   ``exact``
      Whether the result is exact.

   ``mode``
      Combined :class:`SliceMode`.

``adhoc_combine_slices``
------------------------

.. py:function:: adhoc_combine_slices(s1, s2)

   Best-effort slice composition without knowing source length.

   .. code-block:: python

      from pythorn.collections.range import adhoc_combine_slices

      exact = adhoc_combine_slices(slice(None, None, 2), slice(1, 4))
      exact.slice
      exact.exact

``is_full_slice`` and ``slice_len``
-----------------------------------

.. py:function:: is_full_slice(s)
.. py:function:: slice_len(slice1, max_len)

   Helpers for common slice checks.

   .. code-block:: python

      from pythorn.collections.range import is_full_slice, slice_len

      is_full_slice(slice(None, None))
      slice_len(slice(1, 8, 2), 10)

Autodoc
-------

.. automodule:: pythorn.collections.range
   :members:
   :undoc-members:
