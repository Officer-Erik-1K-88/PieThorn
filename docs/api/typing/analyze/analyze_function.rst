analyze Function
================

.. py:function:: analyze(obj)

Purpose
-------

Return an :class:`Info` wrapper for the given object.

Example
-------

.. code-block:: python

   from pythorn.typing.analyze import analyze

   def sample(a, /, b: int, *args, c=3, **kwargs) -> str:
       return "ok"

   info = analyze(sample)
   info.arguments.positional
