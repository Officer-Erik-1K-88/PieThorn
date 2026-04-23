Collections Guide
=================

The ``piethorn.collections`` package is a set of small focused data structures.

Character Helpers
-----------------

``Char``
   Wraps a single character or an empty sentinel and exposes comparison and
   classification methods similar to ``str``.

``CharSequence``
   Normalizes an iterable of characters into an immutable tuple of
   :class:`~piethorn.collections.char.Char` objects. Multi-character strings are
   flattened automatically.

``CharIterator``
   Provides iteration helpers such as peeking, consuming, skipping empty values,
   and optionally skipping whitespace.

Typical uses:

* parser-style input traversal
* normalizing mixed ``str`` and integer character input
* comparing characters by Unicode code point without losing string ergonomics

Mapping Helper
--------------

``Map`` is an ordered mutable mapping backed by parallel key and value lists.
Compared to a normal ``dict``, it exposes index-oriented helpers such as
``key_index()``, ``value_index()``, ``key_at_index()``, and
``value_at_index()``.

Use it when you need:

* deterministic insertion order
* list-style indexed access to keys and values
* an object that still behaves like a mutable mapping

Views
-----

``SequenceView`` exposes a read-only slice or reversed perspective over an
existing sequence without copying it.

``MapView`` wraps any mapping to expose an immutable mapping interface.

``SequenceView`` is especially useful when:

* a function should consume part of a sequence without allocating a copy
* you need nested views that preserve a parent relationship
* you need reverse iteration over a specific cut of a larger sequence

Slice Composition Helpers
-------------------------

The :mod:`piethorn.collections.range` module focuses on composing slices.

``combine_slices()``
   Produces an exact composed slice when the original sequence length is known.

``adhoc_combine_slices()``
   Produces a best-effort result when sequence length is not known. The return
   value includes both the slice and metadata describing whether the result is
   exact.

``SliceMode``
   Classifies slices by how dependent they are on sequence length.

This split is important: exact composition is only possible in some cases
without concrete sequence length information.
