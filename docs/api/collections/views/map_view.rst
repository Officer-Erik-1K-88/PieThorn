MapView Type
============

.. py:class:: MapView(origin)

Purpose
-------

``MapView`` is a read-only wrapper around an existing mapping.

Example
-------

.. code-block:: python

   from piethorn.collections.views import MapView

   view = MapView({"left": 1, "right": 2})
   view["left"]
   view.get("missing", 5)

Methods
-------

``get(key, default=None)``
   Retrieve a key or a default value.
