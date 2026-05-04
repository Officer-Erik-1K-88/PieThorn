Listener Sequence Module
========================

Module: :mod:`piethorn.collections.listener.sequence`

Overview
--------

This module provides abstract sequence base classes that emit listener events
from sequence operations.

``ListenerSequence``
--------------------

.. py:class:: ListenerSequence
   :no-index:

   Read-only sequence base class with a ``get`` listener for ``__getitem__``.

``MutableListenerSequence``
---------------------------

.. py:class:: MutableListenerSequence
   :no-index:

   Mutable sequence base class that extends ``ListenerSequence`` and adds:

   ``add``
      Triggered by ``insert()``.

   ``set``
      Triggered by ``__setitem__()``.

   ``remove``
      Triggered by ``__delitem__()``.

Example
-------

.. code-block:: python

   from piethorn.collections.listener import MutableListenerSequence


   class DemoSequence(MutableListenerSequence[int]):
       def __init__(self, values):
           super().__init__()
           self.values = list(values)

       def __len__(self):
           return len(self.values)

       def __getitem__(self, index):
           return self.values[index]

       def insert(self, index, value):
           self.values.insert(index, value)

       def __setitem__(self, index, value):
           self.values[index] = value

       def __delitem__(self, index):
           del self.values[index]


   sequence = DemoSequence([1, 2])
   sequence.add_listener("add", lambda event: print(event.args) or True)
   sequence.insert(1, 5)

Autodoc
-------

.. automodule:: piethorn.collections.listener.sequence
   :members:
   :undoc-members:
