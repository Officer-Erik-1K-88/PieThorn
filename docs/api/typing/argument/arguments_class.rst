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

``at(index, in_keywords=False)``
   Return an argument by order.

``get_arg(key)``, ``set_arg(arg)``
   Work with the stored argument definitions directly.

``set(key, value)``
   Set a value, optionally creating a new definition when strict keys are off.

``ensure_defaults(**kwargs)``
   Guarantee defaults for certain keys.

``remove(key)``
   Remove and return one argument definition.

``iter_keywords()`` / ``iter_positionals()``
   Iterate stored keys by category.
