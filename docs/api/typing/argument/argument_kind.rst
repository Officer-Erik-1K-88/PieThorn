ArgumentKind Enum
=================

.. py:class:: ArgumentKind

Purpose
-------

``ArgumentKind`` normalizes the binding categories used by
``inspect.Parameter``.

Values
------

``POSITIONAL_OR_KEYWORD``, ``POSITIONAL_ONLY``, ``KEYWORD_ONLY``,
``VAR_POSITIONAL``, ``VAR_KEYWORD``

Method
------

``from_param_kind(param_kind)``
   Convert from an ``inspect.Parameter.kind`` value.
