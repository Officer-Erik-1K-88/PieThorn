Module Wrapper
==============

.. py:class:: Module(..., module_info=None)

Purpose
-------

``Module`` exposes a filesystem-backed package tree as normal Python attribute
access.

Behavior
--------

Attribute lookup checks:

1. the loaded Python module object
2. lazily discovered submodules from ``ModuleInfo``

Example
-------

.. code-block:: python

   info = ModuleInfo(package_path)
   module = info.module
