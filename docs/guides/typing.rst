Typing Guide
============

The ``piethorn.typing`` package contains two related but separate tools.

Runtime Argument Containers
---------------------------

``piethorn.typing.argument`` defines:

``ArgumentKind``
   A normalized enum over the ``inspect.Parameter`` kinds.

``Argument``
   A runtime object that stores a key, accepted type, default value, allowed
   values, current value, and argument kind.

``Arguments``
   A mutable mapping of ``Argument`` definitions and values.

This module is useful when you need:

* runtime validation for argument values
* containers for positional, keyword, and variadic argument shapes
* defaults and type checking outside of static type checkers

Inspection Helpers
------------------

``piethorn.typing.analyze`` wraps the standard library ``inspect`` module and
returns structured metadata.

``analyze(obj)``
   Returns an ``Info`` object.

``Info.arguments``
   Returns an :class:`Arguments <piethorn.typing.analyze.Arguments>` sequence that
   classifies positional-only, positional-or-keyword, and keyword-only
   parameters.

``Info`` predicate methods
   Mirror many ``inspect`` predicates such as ``isfunction()``,
   ``ismethod()``, ``isbuiltin()``, and ``iscoroutinefunction()``.

When To Choose Which Module
---------------------------

Use ``piethorn.typing.argument`` when you need to define or store argument data.

Use ``piethorn.typing.analyze`` when you need to inspect an existing callable or
object and ask structural questions about it.
