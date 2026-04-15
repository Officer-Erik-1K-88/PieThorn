Path Helper Functions
=====================

This page groups the project-root aware helper functions in
:mod:`pythorn.filehandle.importer`.

``with_caller_context(...)``
   Decorator that injects caller and project-root context.

``to_path(...)``
   Resolve path fragments against the tracked root or source directory.

``change_source_dir(...)``
   Validate and update the source directory.

``convert_dot_notation(...)``
   Convert dotted notation to a project-relative file path.

``load_target_module(...)``
   Load a module directly from a file path.
