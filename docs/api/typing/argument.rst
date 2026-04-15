Runtime Argument Module
=======================

Module: :mod:`pythorn.typing.argument`

Overview
--------

This module provides runtime argument definitions and a mutable container for
validated argument values.

.. toctree::
   :maxdepth: 1

   argument/argument_kind
   argument/argument_class
   argument/arguments_class

``ArgumentKind``
----------------

.. py:class:: ArgumentKind

   Enum describing binding semantics:

   * ``POSITIONAL_OR_KEYWORD``
   * ``POSITIONAL_ONLY``
   * ``KEYWORD_ONLY``
   * ``VAR_POSITIONAL``
   * ``VAR_KEYWORD``

   ``from_param_kind(param_kind)``
      Convert an ``inspect.Parameter.kind`` into ``ArgumentKind``.

``Argument``
------------

.. py:class:: Argument(key, type_var, *, allowed_values=empty, kind=ArgumentKind.POSITIONAL_OR_KEYWORD, default=empty, value=empty)

   Runtime description of one argument and its current or default value.

   Example
   ~~~~~~~

   .. code-block:: python

      from pythorn.typing.argument import Argument, ArgumentKind

      positional = Argument("count", int, default=1)
      variadic_kwargs = Argument("options", int, kind=ArgumentKind.VAR_KEYWORD)

   Methods
   ~~~~~~~

   ``from_param(param)``
      Build a runtime argument from an ``inspect.Parameter``.

   ``set_default(default)``
      Validate and set the default.

   ``set(value, *, key=None)``
      Set the current value. Variadic keyword arguments require ``key``.

   ``add(value)``
      Add a value to a variadic argument.

   ``remove(key=None)``
      Remove the current value or a variadic child value.

   ``validate(value, throw=True)``
      Type-check and allowed-value-check a value.

   ``copy(**kwargs)``
      Clone the argument definition.

``Arguments``
-------------

.. py:class:: Arguments(*args, parent=None, strict_keys=True, silent_strict=False, typing_with_value=False)

   Mutable mapping of :class:`Argument` definitions and values.

   Example
   ~~~~~~~

   .. code-block:: python

      from pythorn.typing.argument import Argument, Arguments

      arguments = Arguments(Argument("count", int, default=1), strict_keys=False)
      arguments.set("name", "erik")
      arguments.ensure_defaults(extra=2)

   Methods
   ~~~~~~~

   ``validate(key, value, throw=True)``
      Validate a key/value pair against stored typing information.

   ``at(index, in_keywords=False)``
      Return an :class:`Argument` by positional or keyword order.

   ``get_arg(key)``
      Return the underlying :class:`Argument` definition.

   ``set_arg(arg)``
      Add an argument definition.

   ``set(key, value)``
      Set a value, optionally creating a new argument when strict keys are off.

   ``ensure_defaults(**kwargs)``
      Guarantee defaults for selected keys.

   ``remove(key)``
      Remove and return the stored :class:`Argument`.

   ``iter_keywords()`` / ``iter_positionals()``
      Iterate stored keyword or positional keys.

Autodoc
-------

.. automodule:: pythorn.typing.argument
   :members:
   :undoc-members:
