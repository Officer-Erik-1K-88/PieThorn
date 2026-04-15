Functions Registry
==================

.. py:class:: Functions(*functions)

Purpose
-------

``Functions`` is the ordered registry used to store available equation
functions.

Methods
-------

``append(function)``, ``insert(index, function)``, ``extend(functions)``
   Add functions to the registry.

``get(name)``
   Retrieve one function by name.

``name_index(name, start=0, stop=None)``
   Return a name position.

``names()``
   Return all function names.

``FUNCTIONS``
-------------

The module-level default registry contains the built-in constants and helpers.
