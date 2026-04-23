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

   .. code-block:: python

      declared.check(provided)

``fill(parameters)``
   Copy provided values into this layout.

   .. code-block:: python

      filled = declared.fill(provided)

``required_filled()``
   Return whether all required parameters have values.

``get_named_parameter(name)``
   Fetch a parameter by name.

Typical example
---------------

.. code-block:: python

   from piethorn.math.equation import Parameter, Parameters

   declared = Parameters((
       Parameter("", required=True),
       Parameter("named", default=1),
   ))
   provided = Parameters((
       Parameter("", value=10),
       Parameter("named", value=20),
   ))
