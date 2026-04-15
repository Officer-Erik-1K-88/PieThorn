Top-Level Math Module
=====================

Module: :mod:`pythorn.math`

Overview
--------

The top-level math module exposes boolean gate helpers and a skewed random
number generator.

.. toctree::
   :maxdepth: 1

   top_level/logic_gates
   top_level/skew

``LogicGates``
--------------

.. py:class:: LogicGates(reverse=False)

   Evaluate boolean and boolean-like values with standard gate operations.

   Example
   ~~~~~~~

   .. code-block:: python

      from pythorn.math import LogicGates

      gates = LogicGates()
      gates.and_gate([True, 1, True])
      gates.or_gate(False, 1)
      gates.not_gate([True, False, 1])

   Methods
   ~~~~~~~

   ``and_gate(*boolean)``
   ``or_gate(*boolean)``
   ``not_gate(*boolean)``
   ``nand_gate(*boolean)``
   ``nor_gate(*boolean)``
   ``xor_gate(*boolean)``
   ``xnor_gate(*boolean)``

``skew``
--------

.. py:function:: skew(skew_at=0.6, weight=0.9, minimum=0, maximum=100, is_int=False)

   Generate a bounded random value biased toward ``skew_at``.

   .. code-block:: python

      from pythorn.math import skew

      skew(skew_at=0.4, weight=0.2, minimum=10, maximum=20, is_int=True)

Autodoc
-------

.. automodule:: pythorn.math
   :members:
   :undoc-members:
