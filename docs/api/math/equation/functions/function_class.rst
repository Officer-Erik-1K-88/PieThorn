Function Class
==============

.. py:class:: Function(name, value=None, parameters=None, action=None)

Purpose
-------

Represent either a constant value or a callable function usable in equations.

Key methods
-----------

``is_value()``
   Return whether this function is constant.

   .. code-block:: python

      Function("pi", value="3.14").is_value()

``apply(param_handler=None)``
   Evaluate through a parameter transformer.

   .. code-block:: python

      func.apply(lambda parameters: Parameters((
          parameters[0].new(3),
          parameters[1].new(4),
      )))

``__call__(parameters)``
   Evaluate with a concrete parameter set.

   .. code-block:: python

      func(Parameters((
          Parameter("left", value=3),
          Parameter("right", value=4),
      )))

Behavior notes
--------------

Action-based functions require a declared ``Parameters`` layout. Constant-value
functions ignore parameter handling completely.
