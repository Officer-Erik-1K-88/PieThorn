CounterBehavior Class
=====================

.. py:class:: CounterBehavior(reset_on_reset=True, remove_on_reset=False, affect_child=False)

Purpose
-------

``CounterBehavior`` controls how reset and parent-child interactions work for
``Counter`` and ``Percent`` objects.

Methods
-------

``reset_allowed()``
   Return whether reset changes anything.

``child_behavior(...)``
   Return a child behavior linked to the current one.
