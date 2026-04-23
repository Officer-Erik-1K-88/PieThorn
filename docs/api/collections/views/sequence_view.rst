SequenceView Type
=================

.. py:class:: SequenceView(origin, *, reverse=False, cut=None)

Purpose
-------

``SequenceView`` gives a read-only perspective over part or all of another
sequence.

Examples
--------

.. code-block:: python

   from piethorn.collections.views import SequenceView

   view = SequenceView([1, 2, 3, 4], reverse=True, cut=slice(1, 4))
   nested = view[1:]

   list(view) == [4, 3, 2]
   list(nested) == [3, 2]

Important properties
--------------------

``origin_size``, ``is_reversed``, ``parent``, ``has_parent``, ``cut``,
``has_cut``

Important methods
-----------------

``count(value)``
   Count occurrences in the visible region.

``index(value, start=0, stop=None)``
   Return the view-local index of a value.
