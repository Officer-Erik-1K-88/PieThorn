Logging Guide
=============

The ``piethorn.logging`` package is intentionally small: it provides a logger and
two families of counters for tracking work.

Logger
------

``Logger`` prints tagged messages and tracks how many messages of each type were
emitted.

Important methods:

``base_log()``
   Low-level output helper that prints raw messages when the configured debug
   level allows it.

``log()``, ``error()``, ``warn()``, ``info()``
   Higher-level logging entry points that prefix output with a title such as
   ``[INFO]``.

``log_sep()``
   Prints a separator line, optionally centered around a title.

``count()`` and ``percent()``
   Factory helpers that create counters bound to the logger.

Counters
--------

``Counter``
   Tracks visible, hidden, and fractional progress. It supports absolute adds,
   fractional adds, tick-based progression, and formatted status messages.

``Percent``
   Extends counter behavior with a cap and percent-based progress reporting.

``CounterBehavior``
   Controls how reset behavior propagates through parent/child counter trees.

Design Notes
------------

The counter objects are not just numeric containers. They can also:

* emit messages through the logger they are bound to
* create child counters that influence parent progress
* distinguish visible from hidden work
* support configurable reset propagation

This makes the package more suitable for simple CLI progress reporting than for
general-purpose structured logging.
