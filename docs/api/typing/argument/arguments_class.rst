Runtime Arguments Container
===========================

.. py:class:: Arguments(*args, parent=None, strict_keys=True, silent_strict=False, typing_with_value=False)

Purpose
-------

``Arguments`` is a mutable mapping of :class:`Argument` definitions and their
values.

Key methods
-----------

``validate(key, value, throw=True)``
   Validate a key/value pair.

   .. code-block:: python

      arguments.validate("count", 2)

``at(index, in_keywords=False)``
   Return an argument by order.

   .. code-block:: python

      arguments.at(0)

``get_arg(key)``, ``set_arg(arg)``
   Work with the stored argument definitions directly.

``set(key, value)``
   Set a value, optionally creating a new definition when strict keys are off.

   .. code-block:: python

      arguments.set("name", "erik")

``ensure_defaults(**kwargs)``
   Guarantee defaults for certain keys.

   .. code-block:: python

      arguments.ensure_defaults(extra=2)

``remove(key)``
   Remove and return one argument definition.

``iter_keywords()`` / ``iter_positionals()``
   Iterate stored keys by category.

Behavior notes
--------------

When ``strict_keys`` is ``False``, unknown keys can create new runtime argument
definitions on the fly.
