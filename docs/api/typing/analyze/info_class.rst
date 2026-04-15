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

Example
-------

.. code-block:: python

   from pythorn.typing.analyze import analyze

   def sample(a, /, b: int, *args, c=3, **kwargs) -> str:
       return "ok"

   info = analyze(sample)
   info.callable()
   info.isfunction()
   info.return_annotation
