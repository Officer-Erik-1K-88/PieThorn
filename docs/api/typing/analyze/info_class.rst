Info Class
==========

.. py:class:: Info(obj)

Purpose
-------

``Info`` stores inspection results for an arbitrary object.

Important properties
--------------------

``object``, ``arguments``, ``return_annotation``

Predicate methods
-----------------

``callable()``, ``awaitable()``, ``ismethod()``, ``isfunction()``,
``iscoroutinefunction()``, ``isclass()``, ``ismodule()``, ``isbuiltin()``, and
the other ``inspect``-mirroring helpers exposed by the class.
