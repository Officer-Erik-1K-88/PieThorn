Views Module
============

Module: :mod:`pythorn.collections.views`

Overview
--------

This module provides read-only wrappers over sequences and mappings.

.. toctree::
   :maxdepth: 1

   views/sequence_view
   views/map_view

``SequenceView``
----------------

.. py:class:: SequenceView(origin, *, reverse=False, cut=None)

   Read-only view over an existing sequence.

   Main properties
   ~~~~~~~~~~~~~~~

   ``origin_size``
      Length of the original sequence.

   ``is_reversed``
      Whether iteration is reversed.

   ``parent`` / ``has_parent``
      Parent view information for nested views.

   ``cut`` / ``has_cut``
      Normalized slice applied to the origin.

   Example
   ~~~~~~~

   .. code-block:: python

      from pythorn.collections.views import SequenceView

      view = SequenceView([1, 2, 3, 4], reverse=True, cut=slice(1, 4))
      nested = view[1:]

      list(view)     # [4, 3, 2]
      view[1]        # 3
      list(nested)   # [3, 2]

   Methods
   ~~~~~~~

   ``count(value)``
      Count occurrences in the visible region.

   ``index(value, start=0, stop=None)``
      Return the view-local index of a value.

``MapView``
-----------

.. py:class:: MapView(origin)

   Immutable wrapper around a mapping.

   Example
   ~~~~~~~

   .. code-block:: python

      from pythorn.collections.views import MapView

      view = MapView({"left": 1, "right": 2})
      view["left"]         # 1
      view.get("none", 5)  # 5

Autodoc
-------

.. automodule:: pythorn.collections.views
   :members:
   :undoc-members:
