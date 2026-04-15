File Class
==========

.. py:class:: File(f_path, children=None, parent=None, sisters=None, find_children=True)

Purpose
-------

``File`` wraps a path and adds tree navigation plus simplified I/O operations.

Workflow example
----------------

.. code-block:: python

   from pythorn.filehandle.filehandling import File

   root = File("workspace", find_children=False)
   child = root.create_child("data/example.txt", "hello")
   child.write("first", line=0, insert=True)
   child.write("replaced", line=1, insert=False)

Properties
----------

``file_path``, ``parent``, ``children``, ``sisters``

Methods
-------

``update_children()``
   Refresh the cached child listing.

   .. code-block:: python

      root.update_children()
      root.children

``create_child(f, file_content=None)``
   Create a child file or directory.

   .. code-block:: python

      folder = root.create_child("logs")
      child = root.create_child("logs/app.txt", "booted")

``exists()``, ``isfile()``, ``isdir()``
   Path-state helpers.

   .. code-block:: python

      child.exists()
      child.isfile()
      folder.isdir()

``build(data=None)``
   Create the underlying path.

   .. code-block:: python

      orphan = File("tmp/example.txt", find_children=False)
      orphan.build("hello")

``write(data, line=-1, insert=True, override=False)``
   Append, insert, replace, or override file contents.

``read(hint=-1)``
   Read lines.

   .. code-block:: python

      lines = child.read()

``rig(func, mode="r")``
   Open the file and pass the handle into a callback.

Behavior notes
--------------

``file_path`` is intentionally read-only after construction.

For non-existent paths, ``isfile()`` and ``isdir()`` fall back to a filename
heuristic based on whether the last path segment contains a dot.
