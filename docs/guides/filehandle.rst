Filehandle Guide
================

The ``pythorn.filehandle`` package contains two distinct toolsets:

* a filesystem wrapper centered on :class:`pythorn.filehandle.filehandling.File`
* import and path discovery helpers centered on
  :class:`pythorn.filehandle.importer.CallerRoot`

Working With ``File``
---------------------

``File`` wraps an absolute normalized path and provides convenience methods for
creating directories, creating child files, reading content, and editing files
line-by-line.

Core workflow:

1. Create a root ``File`` for a directory.
2. Call ``create_child()`` for nested directories or files.
3. Use ``build()``, ``write()``, ``read()``, or ``rig()`` for I/O.

Behavior Notes
--------------

``File.isfile()`` and ``File.isdir()``
   Fall back to filename heuristics when the path does not exist yet.

``children`` and ``sisters``
   Return read-only views over discovered ``File`` objects rather than mutable
   internal collections.

``rig()``
   Opens the file and passes the handle into a callable, which is useful when
   you need one-off custom logic without duplicating open/close handling.

Importer Utilities
------------------

The importer helpers are designed for code that needs to locate modules relative
to the caller's project layout.

``CallerRoot``
   Tracks a project root path and source directory.

``to_path()``
   Resolves relative fragments against the tracked project or source directory.

``change_source_dir()``
   Updates the known source directory when a valid path is discovered.

``convert_dot_notation()``
   Converts dotted module names into source-relative paths.

``load_target_module()``
   Loads a module directly from a path without requiring it to be on
   ``sys.path``.

``ModuleInfo``
   Represents filesystem-backed module metadata and can load package trees.

When To Use These Helpers
-------------------------

These utilities are useful when you want project-relative path resolution
without hard-coding repository layout assumptions into each call site.
