Math Guide
==========

The ``pythorn.math`` package has three main areas:

* boolean helpers and skewed random generation in ``pythorn.math``
* number-word conversion in ``pythorn.math.converter``
* decimal equation parsing and evaluation in ``pythorn.math.equation``

Logic Helpers
-------------

``LogicGates`` implements AND, OR, NOT, NAND, NOR, XOR, and XNOR over boolean
or boolean-like inputs. When ``reverse=True`` is used, the truthy and falsy
polarities are inverted.

``skew()``
   Generates a random value in a bounded range, biased toward a configurable
   point.

Converter
---------

The converter module translates between numeric values and English word forms.
It also includes helpers for large-number naming and a text-to-digit obfuscation
helper named ``letter_to_number()``.

Key entry points:

``convert_to_words()``
   Convert numbers into title-cased English wording.

``convert_to_number()``
   Parse numeric strings or supported English phrases into
   :class:`decimal.Decimal`.

``convert_to_big()``
   Coerce several input shapes into a :class:`decimal.Decimal`.

``convert_partial_word()``
   Build a compact partially worded representation using scale names.

Equation Engine
---------------

The equation subsystem parses expressions into a reusable token tree and then
evaluates that tree using :class:`decimal.Decimal`.

Main concepts:

``Equation``
   Parses a source expression once and exposes ``calculate()`` for repeated
   evaluation.

``Variable``
   Represents variable references in the form ``$name$`` or ``$name:default$``.

``Function`` and ``FUNCTIONS``
   Represent callable functions or constant values available to expressions.

``Parameter`` and ``Parameters``
   Describe the expected inputs for equation functions.

Built-In Equation Functions
---------------------------

The default registry includes:

* ``pi`` and ``e`` as constant values
* ``abs(value)``
* ``min(left, right)``
* ``max(left, right)``
* ``clamp(value, minimum, maximum)``
* ``if(condition, when_true, when_false)``

Custom Functions
----------------

Custom equation functions are registered by mutating the module-level
``FUNCTIONS`` collection. A function can either be:

* a constant value function
* an action-based function with declared parameters

Boolean Parameters
------------------

Equation functions can declare parameters with ``takes_boolean=True``. Those
parameters are evaluated with the parser's boolean-comparison rules instead of
numeric-expression rules.

Timing Helpers
--------------

The converter timing helpers provide formatting and UTC conversion utilities for
durations and timestamps. See :mod:`pythorn.math.converter.timing` in the API
reference for the exact entry points.
