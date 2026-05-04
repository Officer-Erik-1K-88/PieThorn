Listenable Module
=================

Module: :mod:`piethorn.collections.listener.listenable`

Overview
--------

This module provides classes for objects that own and dispatch named listeners.

``Listenable``
--------------

.. py:class:: Listenable(*named, listener_builder=None, auto_create=False)
   :no-index:

   Base class for instances that own listeners.

   Example
   ~~~~~~~

   .. code-block:: python

      from piethorn.collections.listener import Listenable, listens


      class Model(Listenable):
          def __init__(self):
              super().__init__("changed")

          @listens("changed")
          def change(self, value):
              return value

   Methods
   ~~~~~~~

   ``get_listener(name)``
      Return a registered listener.

   ``has_listener(name)``
      Return whether a listener exists.

   ``add_listener(name, caller)``
      Add a callback to a named listener.

   ``remove_listener(name, caller)``
      Remove a callback from a named listener.

   ``event_trigger(name, args, kwargs, returned, called_method)``
      Manually dispatch stored call context through a listener.

``ListenerHolder``
------------------

.. py:class:: ListenerHolder(*named, listener_builder=None, auto_create=False)
   :no-index:

   Standalone container-style wrapper around ``ListenerBuilder``.

   ``create(name, replace=False)`` creates or returns a listener in the holder.
   ``remove(name, default=None)`` removes a listener entry.

``GLOBAL_LISTENERS``
--------------------

Process-global ``ListenerHolder`` used by decorated plain functions and by
``Listenable`` methods that do not have a local listener for the requested
event.

Autodoc
-------

.. automodule:: piethorn.collections.listener.listenable
   :members:
   :undoc-members:
