LogicGates Class
================

.. py:class:: LogicGates(reverse=False)

Purpose
-------

``LogicGates`` evaluates boolean and boolean-like values with a small family of
gate operations.

Methods
-------

``and_gate(...)``, ``or_gate(...)``, ``not_gate(...)``, ``nand_gate(...)``,
``nor_gate(...)``, ``xor_gate(...)``, ``xnor_gate(...)``

Example
-------

.. code-block:: python

   from piethorn.math import LogicGates

   gates = LogicGates()
   gates.and_gate([True, 1, True])
