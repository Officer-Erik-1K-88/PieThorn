Listens Module
==============

Module: :mod:`piethorn.collections.listener.listens`

Overview
--------

This module provides decorators and metadata for turning callable execution into
listener events.

``listens()``
-------------

.. py:function:: listens(*listens_for_names, allow_recurse=True, throw_on_recurse_denied=True, straight_call_on_recurse_denied=False, in_use_on_instance=True, inherited_listens_for=DEFAULT_LISTENS_FOR)
   :no-index:

   Decorate a callable so it triggers named listeners after the callable
   returns.

   Example
   ~~~~~~~

   .. code-block:: python

      from piethorn.collections.listener import GLOBAL_LISTENERS, listens

      GLOBAL_LISTENERS.create("done", replace=True)
      GLOBAL_LISTENERS.add_listener("done", lambda event: print(event.args) or True)

      @listens("done")
      def work(value):
          return value * 2

      work(4)

   Behavior
   ~~~~~~~~

   * at least one listener name is required
   * ``Listenable`` instance methods dispatch to the instance first
   * plain functions dispatch to ``GLOBAL_LISTENERS``
   * instance methods fall back to ``GLOBAL_LISTENERS`` when no local listener
     exists
   * ``self`` is removed from ``Event.args`` for ``Listenable`` instance
     methods

``ListensFor``
--------------

.. py:class:: ListensFor(names, allow_recurse=True, throw_on_recurse_denied=True, straight_call_on_recurse_denied=False, in_use_on_instance=True)
   :no-index:

   Metadata attached to callables wrapped by ``listens``.

   ``merge()`` combines inherited metadata with local decorator metadata while
   preserving explicit recursion settings.

``system_listens()``
--------------------

.. py:function:: system_listens(*names, throw_on_recurse_denied=False, straight_call_on_recurse_denied=False)
   :no-index:

   Internal helper for listener-system methods that should emit listener events
   without recursively dispatching themselves.

Autodoc
-------

.. automodule:: piethorn.collections.listener.listens
   :members:
   :undoc-members:
