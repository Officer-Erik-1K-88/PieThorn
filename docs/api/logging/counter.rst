Counter Module
==============

Module: :mod:`piethorn.logging.counter`

Overview
--------

This module provides the progress and percentage counter types used by the
logging package.

.. toctree::
   :maxdepth: 1

   counter/counter_behavior
   counter/counter_class
   counter/percent_class

.. contents::
   :local:
   :depth: 2

``CounterBehavior``
-------------------

.. py:class:: CounterBehavior(reset_on_reset=True, remove_on_reset=False, affect_child=False)

   Controls reset propagation between parent and child counters.

   Key methods
   ~~~~~~~~~~~

   ``reset_allowed()``
      Return whether resetting has any effect.

   ``child_behavior(*args, **kwargs)``
      Return a child behavior linked to this one.

``Counter``
-----------

.. py:class:: Counter(name, visible=0, hidden=0, only_visible=True, *, step=1.0, logger=None, behavior=_DEFAULT_COUNTER_BEHAVIOR)

   General progress counter with visible, hidden, and fractional values.

   Example
   ~~~~~~~

   .. code-block:: python

      from piethorn.logging.counter import Counter

      counter = Counter("jobs", visible=1, hidden=2, only_visible=False, step=0.5)
      counter.add(2)
      counter.float_add(1.25, hidden=True)
      counter.tick(2, worth=2)

   Main properties
   ~~~~~~~~~~~~~~~

   * ``behavior``
   * ``name``
   * ``long_name``
   * ``visible``
   * ``hidden``
   * ``decimal``
   * ``total``
   * ``current``
   * ``step``

   Methods
   ~~~~~~~

   ``build_message(compact=False, allow_lr=False)``
      Return the default message fragments used for logging.

   ``message_send(...)``
      Send or build a logger message for this counter.

   ``add(amount, hidden=False)``
      Add an integer amount.

   ``float_add(amount, hidden=False)``
      Add a floating-point amount, preserving the fractional portion.

   ``tick_worth(tick_count, worth, linear)``
      Compute how much one tick contributes before multiplication by ``step``.

   ``tick(tick_count=1, worth=1.0, linear=True, hidden=False)``
      Add one tick-based increment.

      .. code-block:: python

         counter.tick(2, worth=2)

   ``non_linear_tick(tick_count=1, worth=1.0, hidden=False)``
      Expand non-linear tick progression across each intermediate tick.

   ``reset()``
      Reset the counter according to its behavior.

   ``check()``
      Extension hook. The base counter does nothing.

   ``compare(other)``
      Three-way numeric comparison helper.

``Percent``
-----------

.. py:class:: Percent(name, current=0, cap=100, step=1, *, logger=None, behavior=_DEFAULT_COUNTER_BEHAVIOR)

   Percentage-oriented counter with optional parent/child relationships.

   Example
   ~~~~~~~

   .. code-block:: python

      from piethorn.logging.counter import Percent

      parent = Percent("task", current=10, cap=20, step=5)
      child = parent("child", cap=5, worth=4)
      child.current = 5
      child.check()

   Additional properties
   ~~~~~~~~~~~~~~~~~~~~~

   * ``parent``
   * ``children``
   * ``long_name``
   * ``percent``
   * ``cap``
   * ``worth``

   Additional methods
   ~~~~~~~~~~~~~~~~~~

   ``__call__(name, current=0, cap=100, step=1, worth=0, child_behavior=None)``
      Create and attach a child percent counter.

   ``larger_percent()``
      Return a 0-100 percentage value.

   ``is_child()``, ``is_parent()``, ``is_complete()``
      Relationship and completion helpers.

   ``build_message(compact=False, allow_lr=False)``
      Return a completion-oriented message description.

   ``check()``
      Propagate child completion into parent progress.

   ``reset()``
      Reset this percent and optionally reset or remove children.

Autodoc
-------

.. automodule:: piethorn.logging.counter
   :members:
   :undoc-members:
