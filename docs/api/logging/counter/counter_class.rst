Counter Class
=============

.. py:class:: Counter(name, visible=0, hidden=0, only_visible=True, *, step=1.0, logger=None, behavior=_DEFAULT_COUNTER_BEHAVIOR)

Purpose
-------

``Counter`` tracks visible, hidden, and fractional progress.

Examples
--------

.. code-block:: python

   from pythorn.logging.counter import Counter

   counter = Counter("jobs", visible=1, hidden=2, only_visible=False, step=0.5)
   counter.add(2)
   counter.float_add(1.25, hidden=True)
   counter.tick(2, worth=2)

Key methods
-----------

``build_message(...)`` / ``message_send(...)``
   Message helpers for logger integration.

``add(...)`` / ``float_add(...)``
   Increment helpers.

``tick_worth(...)`` / ``tick(...)`` / ``non_linear_tick(...)``
   Tick-based progression helpers.

``reset()``, ``check()``, ``compare(other)``
   Lifecycle and comparison helpers.
