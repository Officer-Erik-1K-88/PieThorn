Parameters Class
================

.. py:class:: Parameters(parameters=None)

Purpose
-------

``Parameters`` is an ordered collection of equation parameters with name-based
lookup helpers.

Methods
-------

``check(parameters)``
   Validate another parameter set against this layout.

``fill(parameters)``
   Copy provided values into this layout.

``required_filled()``
   Return whether all required parameters have values.

``get_named_parameter(name)``
   Fetch a parameter by name.
