Listener Module
===============

Module: :mod:`piethorn.collections.listener.listener`

Overview
--------

This module provides named callback chains and the registry that stores them.

``Listener``
------------

.. py:class:: Listener(name, event_builder=DEFAULT_EVENT_BUILDER)
   :no-index:

   Named callback chain that receives ``Event`` objects.

   Example
   ~~~~~~~

   .. code-block:: python

      from piethorn.collections.listener import Listener

      listener = Listener("changed")
      listener.add(lambda event: print(event.returned) or True)
      listener.use((1,), {}, 1, lambda value: value)

   Important methods
   ~~~~~~~~~~~~~~~~~

   ``add(caller)``
      Append a callback. The callback must accept an ``Event``.

   ``remove(caller)``
      Remove a callback from the chain.

   ``use(args, kwargs, returned, called_method)``
      Build an event and dispatch it through the callbacks.

   ``event(args, kwargs, returned, called_method, *, caller=None)``
      Build the event without dispatching it.

   ``get(index)``
      Return a callback by position.

``ListenerBuilder``
-------------------

.. py:class:: ListenerBuilder(default_event_builder=DEFAULT_EVENT_BUILDER)
   :no-index:

   Mutable registry for named listeners.

   ``add(name, replace=False)`` stores a listener. Existing entries are reused
   unless ``replace=True`` is passed.

   Integer names normalize to ``event_{number}``. For example, ``1`` becomes
   ``"event_1"``.

``GetListenerError``
--------------------

.. py:exception:: GetListenerError
   :no-index:

   Raised when a requested listener cannot be found.

Autodoc
-------

.. automodule:: piethorn.collections.listener.listener
   :members:
   :undoc-members:
