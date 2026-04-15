Character Module
================

Module: :mod:`pythorn.collections.char`

Overview
--------

This module provides three related types:

* :class:`Char` for a single normalized character
* :class:`CharSequence` for immutable normalized character collections
* :class:`CharIterator` for parser-style traversal

.. toctree::
   :maxdepth: 1

   char/char_type
   char/char_sequence
   char/char_iterator

``Char``
--------

.. py:class:: Char(char)

   Normalizes one character-like input into a reusable wrapper.

   Accepted input forms:

   * another :class:`Char`
   * an integer Unicode code point
   * a one-character string
   * an empty string sentinel

   Examples
   ~~~~~~~~

   .. code-block:: python

      from pythorn.collections.char import Char

      Char("A").ord() == 65
      Char(65).char() == "A"
      Char("").is_empty() is True

   Methods
   ~~~~~~~

   ``char()``
      Return the wrapped character string.

   ``ord()``
      Return the stored ordinal.

   ``is_empty()``
      Return ``True`` when this is the empty-string sentinel.

   ``compare(other)``
      Compare against another ``Char``, a string, or a number and return
      ``-1``, ``0``, or ``1``.

      .. code-block:: python

         Char("A").compare("B")  # -1
         Char("A").compare(65)   # 0

   ``upper()`` and ``lower()``
      Return new :class:`Char` instances with case converted.

   ``isascii()``, ``isdecimal()``, ``isdigit()``, ``isnumeric()``,
   ``isalnum()``, ``isalpha()``, ``islower()``, ``isupper()``,
   ``isspace()``, ``isprintable()``
      Mirror the corresponding string predicates on the wrapped value.

``CharSequence``
----------------

.. py:class:: CharSequence(chars)

   Immutable sequence of :class:`Char` objects.

   Multi-character strings are flattened during construction.

   Examples
   ~~~~~~~~

   .. code-block:: python

      from pythorn.collections.char import CharSequence

      seq = CharSequence(["ab", " ", "C"])
      str(seq) == "ab C"
      seq[0]
      seq[1:]

   Methods and behavior
   ~~~~~~~~~~~~~~~~~~~~

   ``__getitem__``
      Integer indexing returns :class:`Char`; slicing returns
      :class:`CharSequence`.

   ``__add__``, ``__mul__``, ``__rmul__``
      Preserve the ``CharSequence`` type.

      .. code-block:: python

         CharSequence("ab") + CharSequence("!")  # "ab!"
         CharSequence("ab") * 2                  # "abab"

   ``is_empty()``
      Return ``True`` only if every element is empty.

   ``isascii()``, ``isdecimal()``, ``isdigit()``, ``isnumeric()``,
   ``isalnum()``, ``isalpha()``, ``islower()``, ``isupper()``,
   ``isspace()``, ``isprintable()``
      Apply the corresponding check across the entire sequence.

``CharIterator``
----------------

.. py:class:: CharIterator(chars, *, skip_space=False, skip_empty=False, start_index=0)

   Iterator for sequential parsing over a :class:`CharSequence`.

   Important properties:

   ``current``
      The current consumed character or an empty sentinel.

   ``skip_space``
      Whether whitespace is skipped.

   ``pos``
      Current iterator index.

   ``ate_next``
      Whether :meth:`eat` already consumed the next character.

   Common usage
   ~~~~~~~~~~~~

   .. code-block:: python

      from pythorn.collections.char import CharIterator

      it = CharIterator(["", " ", "a", "b"], skip_space=True, skip_empty=True)
      assert it.peek() == "a"
      assert it.eat("a") is True
      assert next(it) == "b"

   Methods
   ~~~~~~~

   ``char_count()``
      Return the total normalized character count.

   ``has_current()``, ``has_next()``, ``next_ended()``
      State helpers for parsing loops.

   ``eat(char)``
      Consume the next available character only if it matches.

   ``next()`` / ``__next__()``
      Advance to the next available character.

   ``peek()``
      Return the next available character without advancing.

   ``peek_check(action)``
      Call ``action`` with the next available character.

   ``for_remaining(action)``
      Run an action over the rest of the input.

Autodoc
-------

.. automodule:: pythorn.collections.char
   :members:
   :undoc-members:
