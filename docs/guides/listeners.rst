Listeners Guide
===============

The ``piethorn.collections.listener`` package provides a small event system for
attaching callbacks to function and method calls.

Core Pieces
-----------

``Listenable``
   Base class for objects that own named listeners.

``Listener``
   A named callback chain. Each callback receives an ``Event`` and may return
   ``False`` to stop the rest of that chain.

``Event``
   Runtime context for a listener callback. It exposes ``args``, ``kwargs``,
   ``returned``, ``called_method``, ``listener``, and ``caller``.

``listens()``
   Decorator that calls the wrapped function first, then dispatches the
   configured listener events.

Instance Listeners
------------------

Subclass ``Listenable``, create named listeners in ``__init__()``, and decorate
methods with ``@listens``.

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
   seen = []

   counter.add_listener(
       "changed",
       lambda event: seen.append((event.args, event.returned)) or True,
   )

   counter.set_value(3)

   assert seen == [((3,), 3)]

For instance methods on ``Listenable`` objects, ``self`` is removed from
``Event.args``. The event records the meaningful arguments passed by the caller.

Global Listeners
----------------

Decorated plain functions, static methods, and class methods use
``GLOBAL_LISTENERS`` when no ``Listenable`` instance is available.

.. code-block:: python

   from piethorn.collections.listener import GLOBAL_LISTENERS, listens

   GLOBAL_LISTENERS.create("finished", replace=True)
   GLOBAL_LISTENERS.add_listener(
       "finished",
       lambda event: print(event.returned) or True,
   )

   @listens("finished")
   def run_task(name):
       return f"{name} done"

   run_task("build")

When an instance method is called on a ``Listenable`` object, the instance
listener wins. If the instance does not have a matching listener, the decorator
falls back to ``GLOBAL_LISTENERS`` when a global listener exists.

Multiple Events
---------------

A method can trigger more than one listener. Listeners fire in decorator order
after the wrapped method returns.

.. code-block:: python

   class Store(Listenable):
       def __init__(self):
           super().__init__("saved", "changed")

       @listens("saved", "changed")
       def save(self, value):
           return value

Callback Control
----------------

Callbacks control dispatch in three common ways:

* return ``False`` to stop the current listener's remaining callback chain
* call ``event.stop_chain()`` to stop the listener chain after the current
  callback finishes
* call ``event.end(force=True)`` to stop immediately by raising ``EventEnd``

.. code-block:: python

   calls = []

   def first(event):
       calls.append("first")
       return False

   def second(event):
       calls.append("second")
       return True

   counter.add_listener("changed", first)
   counter.add_listener("changed", second)
   counter.set_value(4)

   assert calls == ["first"]

``event.stop_current()`` is most useful when a ``Listener`` is used as a
callback for another ``Listener`` and only the current nested chain should stop.

Recursion Behavior
------------------

``listens()`` protects against recursive listener dispatch. By default,
recursive calls are allowed. Set ``allow_recurse=False`` to deny recursive event
dispatch for a decorated function.

.. code-block:: python

   @listens("changed", allow_recurse=False, throw_on_recurse_denied=False)
   def update(value):
       return value

When recursion is denied, the wrapper can raise ``RecursionError``, return
``None``, or call the wrapped function directly, depending on
``throw_on_recurse_denied`` and ``straight_call_on_recurse_denied``.

Automatic Listener Creation
---------------------------

``Listenable(auto_create=True)`` and ``ListenerHolder(auto_create=True)`` create
missing listeners when ``add_listener()`` is called.

.. code-block:: python

   from piethorn.collections.listener import ListenerHolder

   holder = ListenerHolder(auto_create=True)
   holder.add_listener("created_late", lambda event: True)

Manual Listener Registries
--------------------------

Use ``ListenerHolder`` when you need a standalone registry instead of a full
domain object.

.. code-block:: python

   holder = ListenerHolder("ready")
   holder.add_listener("ready", lambda event: True)
   holder.event_trigger("ready", (), {}, None, lambda: None)

Sequence Base Classes
---------------------

``ListenerSequence`` and ``MutableListenerSequence`` are abstract sequence base
classes that emit listeners from sequence operations.

``ListenerSequence`` creates a ``get`` listener for ``__getitem__``.
``MutableListenerSequence`` adds ``add``, ``set``, and ``remove`` listeners for
``insert()``, ``__setitem__()``, and ``__delitem__()``.

Inheritance
-----------

``Listenable`` preserves listener metadata when a subclass overrides a decorated
member. This lets subclasses customize behavior without repeating the same
``@listens`` declaration on every override.
