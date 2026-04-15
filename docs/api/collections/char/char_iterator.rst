CharIterator Type
=================

.. py:class:: CharIterator(chars, *, skip_space=False, skip_empty=False, start_index=0)

Purpose
-------

``CharIterator`` provides parser-friendly sequential traversal over character
input.

Typical workflow
----------------

.. code-block:: python

   from pythorn.collections.char import CharIterator

   iterator = CharIterator(["", " ", "a", "b"], skip_space=True, skip_empty=True)
   iterator.peek()
   iterator.eat("a")
   next(iterator)

State properties
----------------

``current``
   Last consumed character.

``skip_space``
   Whether whitespace is skipped.

``pos``
   Current index.

``ate_next``
   Whether ``eat`` already consumed the next token.

Methods
-------

``char_count()``, ``has_current()``, ``has_next()``, ``next_ended()``
   State helpers.

``eat(char)``
   Conditionally consume the next character.

``next()`` / ``__next__()``
   Advance iteration.

``peek()``, ``peek_check(action)``
   Look ahead without consuming.

``for_remaining(action)``
   Process the rest of the stream.
