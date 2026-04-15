CharSequence Type
=================

.. py:class:: CharSequence(chars)

Purpose
-------

``CharSequence`` is an immutable sequence of :class:`Char` objects that
normalizes mixed character-like inputs.

Key behavior
------------

* multi-character strings are flattened
* slicing returns another ``CharSequence``
* concatenation and repetition preserve the type

Examples
--------

.. code-block:: python

   from pythorn.collections.char import CharSequence

   sequence = CharSequence(["ab", " ", "C"])
   str(sequence) == "ab C"
   sequence[0]
   sequence[1:]
   sequence * 2

Important methods
-----------------

``is_empty()``
   Return ``True`` only if all elements are empty.

``isascii()``, ``isdecimal()``, ``isdigit()``, ``isnumeric()``, ``isalnum()``,
``isalpha()``, ``islower()``, ``isupper()``, ``isspace()``, ``isprintable()``
   Apply the corresponding character test across the whole sequence.
