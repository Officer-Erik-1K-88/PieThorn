Filehandling Module
===================

Module: :mod:`piethorn.filehandle.filehandling`

Overview
--------

This module groups together path wrappers and JSON persistence helpers.

.. toctree::
   :maxdepth: 1

   filehandling/file_class
   filehandling/json_encoder
   filehandling/json_file

.. contents::
   :local:
   :depth: 2

``File``
--------

.. py:class:: File(f_path, children=None, parent=None, sisters=None, find_children=True)

   Wrap a filesystem path and expose convenience helpers for building trees and
   reading or writing files.

   Example workflow
   ~~~~~~~~~~~~~~~~

   .. code-block:: python

      from piethorn.filehandle.filehandling import File

      root = File("workspace", find_children=False)
      folder = root.create_child("data")
      child = root.create_child("data/example.txt", "hello")
      child.write("second line")

   Properties
   ~~~~~~~~~~

   ``file_path``
      Absolute normalized path string.

   ``parent``
      Parent path as another :class:`File`.

   ``children``
      Read-only child collection.

   ``sisters``
      Read-only sibling collection.

   Methods
   ~~~~~~~

   ``update_children()``
      Refresh child discovery when the path is a directory.

   ``create_child(f, file_content=None)``
      Create a child file or directory beneath this path.

   ``exists()``, ``isfile()``, ``isdir()``
      State helpers for path type and existence.

   ``build(data=None)``
      Create the underlying file or directory.

   ``write(data, line=-1, insert=True, override=False)``
      Append, insert, replace, or fully override file content.

      .. code-block:: python

         child.write("first", line=0, insert=True)
         child.write("replaced", line=1, insert=False)

   ``read(hint=-1)``
      Read lines from the file.

   ``rig(func, mode="r")``
      Open the file and pass the handle to a callback.

      .. code-block:: python

         text = child.rig(lambda handle: handle.read())

``JSONEncoder``
---------------

.. py:class:: JSONEncoder(...)

   Custom JSON encoder that prefers compact encoding for primitive structures
   and a more expanded layout for nested complex data when indentation is used.

   Key methods
   ~~~~~~~~~~~

   ``dumps(obj)``
      Return a JSON string using the encoder configuration.

   ``iterencode(obj)``
      Yield encoded chunks using the custom formatting logic.

   Example
   ~~~~~~~

   .. code-block:: python

      from piethorn.filehandle.filehandling import JSONEncoder

      JSONEncoder(sort_keys=True).dumps({"b": [1], "a": {"c": 2}})

``JSONFile``
------------

.. py:class:: JSONFile(f_path=None, data=None, mother=None)

   Mutable mapping that persists its state to JSON, either in a real file or as
   a nested view over another :class:`JSONFile`.

   Construction patterns
   ~~~~~~~~~~~~~~~~~~~~~

   * ``JSONFile("config.json")`` for a file-backed mapping
   * nested dict access returns another ``JSONFile`` sharing the parent store

   Example
   ~~~~~~~

   .. code-block:: python

      from piethorn.filehandle.filehandling import JSONFile

      config = JSONFile("config.json")
      config["debug"] = True
      config.setdefault("retries", 3)

   Methods
   ~~~~~~~

   ``exists()``
      Return whether the file or nested JSON key exists.

   ``has_path()`` / ``has_mother()``
      Return whether the object is bound to a path and whether it is nested.

   ``load()``
      Reload current state from backing storage.

   ``save()``
      Persist current state.

   ``get(key, default=None)``
      Reload first, then fetch the key.

   ``fast_get(key, default=None)``
      Fetch from in-memory state without reloading.

   ``setdefault(key, default=None)``
      Set and persist a default value if missing.

   ``pop(key)``, ``popitem()``, ``clear()``
      Mutate and immediately persist.

   ``pathed_as(other)``
      Return whether another ``JSONFile`` points at the same backing location.

Autodoc
-------

.. automodule:: piethorn.filehandle.filehandling
   :members:
   :undoc-members:
