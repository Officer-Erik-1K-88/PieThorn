Runtime Argument Class
======================

.. py:class:: Argument(key, type_var, *, allowed_values=empty, kind=ArgumentKind.POSITIONAL_OR_KEYWORD, default=empty, value=empty)

Purpose
-------

``Argument`` is a runtime container for one typed argument definition and its
value.

Key methods
-----------

``from_param(param)``
   Build from an ``inspect.Parameter``.

   .. code-block:: python

      import inspect

      param = next(iter(inspect.signature(lambda x: x).parameters.values()))
      Argument.from_param(param)

``set_default(default)``, ``set(value, *, key=None)``
   Set the default or current value.

   .. code-block:: python

      arg.set_default(2)
      arg.set(5)

``add(value)``, ``remove(key=None)``
   Manage variadic argument storage.

``validate(value, throw=True)``
   Type-check a proposed value.

   .. code-block:: python

      arg.validate(3)

``copy(**kwargs)``
   Clone the definition.

Behavior notes
--------------

Variadic keyword arguments store their values inside an internal
``Arguments`` container keyed by the provided ``key`` values.
