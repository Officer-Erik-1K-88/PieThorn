Listener Package
================

Module: :mod:`piethorn.collections.listener`

Overview
--------

The listener package provides callback chains that can be attached to decorated
function and method calls.

Use ``Listenable`` for objects that own named listeners, ``listens`` to decorate
callables, and ``Event`` to inspect the call context passed to listener
callbacks.

.. toctree::
   :maxdepth: 1

   listener/event
   listener/listener
   listener/listenable
   listener/listens
   listener/sequence

Quick Example
-------------

.. code-block:: python

   from piethorn.collections.listener import Listenable, listens


   class Counter(Listenable):
       def __init__(self):
           super().__init__("changed")
           self.value = 0

       @listens("changed")
       def set_value(self, value):
           self.value = value
           return self.value


   counter = Counter()
   counter.add_listener("changed", lambda event: print(event.returned) or True)
   counter.set_value(10)

Exported Names
--------------

``Event`` / ``EventBuilder`` / ``EventEnd``
   Event state and construction helpers.

``Listener`` / ``ListenerBuilder`` / ``GetListenerError``
   Callback chain and registry primitives.

``Listenable`` / ``ListenerHolder`` / ``GLOBAL_LISTENERS``
   Runtime objects that own listener registries.

``listens``
   Decorator that dispatches configured listener events after a callable runs.

``ListenerSequence`` / ``MutableListenerSequence``
   Abstract sequence base classes that emit sequence-operation events.

Autodoc
-------

.. automodule:: piethorn.collections.listener
   :members:
   :undoc-members:
   :no-index:
