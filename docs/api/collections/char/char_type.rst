Char Type
=========

.. py:class:: Char(char)

Purpose
-------

``Char`` is a single-character normalization wrapper. It keeps the convenience
of string predicates while also supporting ordinal comparisons and explicit
empty-sentinel handling.

Construction
------------

Accepted inputs:

* another :class:`Char`
* an ``int`` code point
* a one-character ``str``
* an empty string

Examples
--------

.. code-block:: python

   from piethorn.collections.char import Char

   Char(Char("A")).ord() == 65
   Char(65).char() == "A"
   Char("").is_empty() is True

Methods
-------

``char()``
   Return the string form.

``ord()``
   Return the numeric ordinal.

``compare(other)``
   Compare against ``Char``, ``str``, or numeric values.

``upper()`` / ``lower()``
   Return new ``Char`` instances with case conversion.

Predicate methods
-----------------

``is_empty()``, ``isascii()``, ``isdecimal()``, ``isdigit()``, ``isnumeric()``,
``isalnum()``, ``isalpha()``, ``islower()``, ``isupper()``, ``isspace()``,
``isprintable()``

These mirror the wrapped string's behavior.
