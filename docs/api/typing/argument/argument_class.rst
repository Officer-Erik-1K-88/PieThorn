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

``set_default(default)``, ``set(value, *, key=None)``
   Set the default or current value.

``add(value)``, ``remove(key=None)``
   Manage variadic argument storage.

``validate(value, throw=True)``
   Type-check a proposed value.

``copy(**kwargs)``
   Clone the definition.
