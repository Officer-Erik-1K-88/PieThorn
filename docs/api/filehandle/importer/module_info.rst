ModuleInfo Class
================

.. py:class:: ModuleInfo(path, *, name=None, submodules=None)

Purpose
-------

``ModuleInfo`` stores metadata for a module or package on disk and can lazily
build runtime wrappers for it.

Properties
----------

``import_name``, ``name``, ``path``, ``parent``, ``sub_modules``, ``module``,
``is_built``

Methods
-------

``build_module()``
   Build the runtime module and known submodules.

``build_submodules()``
   Build only child modules.

Example
-------

.. code-block:: python

   info = ModuleInfo(package_path)
   module = info.module
   info.is_built
