Event Module
============

Module: :mod:`piethorn.collections.listener.event`

Overview
--------

This module defines the event objects passed to callbacks and the builder that
controls event creation and reuse.

``Event``
---------

.. py:class:: Event(builder, caller)
   :no-index:

   Runtime context passed to listener callbacks.

   Important properties
   ~~~~~~~~~~~~~~~~~~~~

   ``name``
      Display-style event name derived from the listener.

   ``args`` / ``kwargs``
      Arguments passed to the decorated callable. For ``Listenable`` instance
      methods, ``self`` is excluded.

   ``returned``
      Value returned by the decorated callable.

   ``called_method``
      Callable that triggered the event.

   ``listener`` / ``caller``
      Listener associated with the event builder and listener currently
      dispatching the event.

   Dispatch control
   ~~~~~~~~~~~~~~~~

   ``stop_current(force=True)``
      Stop the current chain item.

   ``stop_chain(force=False)``
      Stop the rest of the listener callback chain.

   ``end(force=False)``
      Stop both the current chain item and the remaining chain.

``EventBuilder``
----------------

.. py:class:: EventBuilder(listener=None, static=False, copies_to_new=False)
   :no-index:

   Factory for ``Event`` objects.

   ``static=True`` reuses a cached event until ``clear_event()`` is called.
   ``copies_to_new=True`` makes ``new_listener()`` return a copied builder when
   assigning it to another listener.

``EventEnd``
------------

.. py:exception:: EventEnd(event)
   :no-index:

   Raised internally when a callback force-ends an event.

Autodoc
-------

.. automodule:: piethorn.collections.listener.event
   :members:
   :undoc-members:
