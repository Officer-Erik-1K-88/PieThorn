CallerRoot Class
================

.. py:class:: CallerRoot(path=EMPTY_PATH, source_dir=None, allow_path_changes=True, allow_source_changes=True)

Purpose
-------

``CallerRoot`` stores a project root and source directory that can be reused by
the importer helpers.

Properties
----------

``path``, ``has_path``, ``source_dir``, ``parent``, ``children``

Method
------

``child(path, source_dir=None)``
   Return or create a cached child ``CallerRoot``.
