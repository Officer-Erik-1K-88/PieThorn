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

``apply(param_handler=None)``
   Evaluate through a parameter transformer.

``__call__(parameters)``
   Evaluate with a concrete parameter set.
