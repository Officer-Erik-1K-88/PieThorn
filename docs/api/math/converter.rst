Converter Module
================

Module: :mod:`pythorn.math.converter`

Overview
--------

This module translates between numbers and English wording and includes a few
helper conversions for large magnitudes and text-to-digit obfuscation.

.. toctree::
   :maxdepth: 1

   converter/conversion_functions
   converter/letter_to_number

``find_number_name``
--------------------

.. py:function:: find_number_name(exponent)

   Return the scale word for a decimal exponent.

``find_number_name_from_value``
-------------------------------

.. py:function:: find_number_name_from_value(number)

   Return a scale-name pair for a decimal magnitude.

``convert_to_words``
--------------------

.. py:function:: convert_to_words(number)

   Convert a number to an English phrase.

   .. code-block:: python

      from pythorn.math.converter import convert_to_words

      convert_to_words(0)      # "Zero"
      convert_to_words(12.5)   # "Twelve and Five Tenth"

``convert_partial_word``
------------------------

.. py:function:: convert_partial_word(number, places_before_word=0, round_to=2147483647)

   Produce a compact numeric-plus-scale representation.

   .. code-block:: python

      convert_partial_word(1234567, 2, 4)  # "1234.567 Thousand"

``convert_to_number``
---------------------

.. py:function:: convert_to_number(number_words)

   Parse a numeric string or English phrase into :class:`decimal.Decimal`.

``convert_to_big``
------------------

.. py:function:: convert_to_big(number)

   Coerce several input types into :class:`decimal.Decimal`.

``letter_to_number``
--------------------

.. py:function:: letter_to_number(sentence, percent_to_convert=-1.0)

   Replace supported characters with lookalike digits based on a percentage.

Autodoc
-------

.. automodule:: pythorn.math.converter
   :members:
   :undoc-members:
