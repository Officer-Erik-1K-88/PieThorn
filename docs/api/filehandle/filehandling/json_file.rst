JSONFile Class
==============

.. py:class:: JSONFile(f_path=None, data=None, mother=None)

Purpose
-------

``JSONFile`` is a mutable mapping backed by a JSON document or a nested JSON
sub-object.

Example
-------

.. code-block:: python

   from pythorn.filehandle.filehandling import JSONFile

   config = JSONFile("config.json")
   config["debug"] = True
   config.setdefault("retries", 3)

Methods
-------

``exists()``, ``has_path()``, ``has_mother()``
   Storage-state helpers.

``load()`` / ``save()``
   Synchronize in-memory data with storage.

``get(key, default=None)`` / ``fast_get(key, default=None)``
   Reloading and non-reloading retrieval helpers.

``setdefault(key, default=None)``, ``pop(key)``, ``popitem()``, ``clear()``
   Mutate and persist immediately.

``pathed_as(other)``
   Return whether another ``JSONFile`` points at the same storage location.
