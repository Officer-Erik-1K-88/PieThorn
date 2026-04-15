Percent Class
=============

.. py:class:: Percent(name, current=0, cap=100, step=1, *, logger=None, behavior=_DEFAULT_COUNTER_BEHAVIOR)

Purpose
-------

``Percent`` adds caps, completion semantics, and child counters on top of
``Counter``.

Examples
--------

.. code-block:: python

   from pythorn.logging.counter import Percent

   parent = Percent("task", current=10, cap=20, step=5)
   child = parent("child", cap=5, worth=4)
   child.current = 5
   child.check()

Key properties
--------------

``parent``, ``children``, ``long_name``, ``percent``, ``cap``, ``worth``

Key methods
-----------

``__call__(...)``
   Create and attach a child percent counter.

``larger_percent()``
   Return the percent in the 0-100 range.

``is_child()``, ``is_parent()``, ``is_complete()``
   Relationship and completion helpers.

``build_message(...)``, ``check()``, ``reset()``
   Progress and propagation behavior.
