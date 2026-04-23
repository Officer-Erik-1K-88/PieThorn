Importer Module
===============

Module: :mod:`piethorn.filehandle.importer`

Overview
--------

This module provides project-root discovery, source-directory tracking, direct
module loading, and runtime wrappers around package trees.

.. toctree::
   :maxdepth: 1

   importer/caller_root
   importer/path_helpers
   importer/module_info
   importer/module_wrapper

.. contents::
   :local:
   :depth: 2

``CallerRoot``
--------------

.. py:class:: CallerRoot(path=EMPTY_PATH, source_dir=None, allow_path_changes=True, allow_source_changes=True)

   Tracks a project root path and optional source directory.

   Important properties:

   * ``path``
   * ``has_path``
   * ``source_dir``
   * ``parent``
   * ``children``

   Methods
   ~~~~~~~

   ``child(path, source_dir=None)``
      Return or create a cached child root.

``with_caller_context``
-----------------------

.. py:function:: with_caller_context(*, needs_caller_root=False, check_output=False, out=Any)

   Decorator used by the importer helpers to inject project-root and caller-root
   context.

``to_path``
-----------

.. py:function:: to_path(*args, sub_to_source=False, resolve=False, strict=False, project_root=_PROJECT_ROOT)

   Resolve one or more path fragments relative to the current tracked project or
   source directory.

   .. code-block:: python

      to_path("child.py", sub_to_source=True, project_root=caller_root)

``change_source_dir``
---------------------

.. py:function:: change_source_dir(source_dir, *, path=None, strict=False, project_root=_PROJECT_ROOT)

   Validate and update the tracked source directory.

   .. code-block:: python

      change_source_dir("pkg", path=root, project_root=caller_root)

``convert_dot_notation``
------------------------

.. py:function:: convert_dot_notation(s, *, project_root=_PROJECT_ROOT)

   Convert dotted import notation into an existing project-relative path.

   .. code-block:: python

      convert_dot_notation("child", project_root=caller_root)  # "child.py"

``load_target_module``
----------------------

.. py:function:: load_target_module(name, path, at_local=False)

   Load a Python module directly from a filesystem path and register it in
   ``sys.modules``.

``ModuleInfo``
--------------

.. py:class:: ModuleInfo(path, *, name=None, submodules=None)

   Metadata object describing a filesystem-backed module or package.

   Important properties:

   * ``import_name``
   * ``name``
   * ``path``
   * ``parent``
   * ``sub_modules``
   * ``module``
   * ``is_built``

   Important methods:

   ``build_module()``
      Build the runtime :class:`Module` and then build submodules.

   ``build_submodules()``
      Build the submodules already registered under this module.

   Example
   ~~~~~~~

   .. code-block:: python

      info = ModuleInfo(package_path)
      module = info.module

``Module``
----------

.. py:class:: Module(..., module_info=None)

   Runtime wrapper that exposes a package tree as attributes and lazily builds
   child modules.

   Behavior
   ~~~~~~~~

   Attribute lookup checks:

   1. the loaded Python module object
   2. known submodule metadata on disk

Autodoc
-------

.. automodule:: piethorn.filehandle.importer
   :members:
   :undoc-members:
