Conversion Functions
====================

This page groups the number-word conversion functions from
:mod:`pythorn.math.converter`.

``find_number_name(exponent)``
   Return the scale name for an exponent.

``find_number_name_from_value(number)``
   Return a scale-name pair for a decimal magnitude.

``convert_to_words(number)``
   Convert a number to words.

``convert_partial_word(number, places_before_word=0, round_to=2147483647)``
   Produce a compact number-plus-scale representation.

``convert_to_number(number_words)``
   Convert supported text back into a :class:`decimal.Decimal`.

``convert_to_big(number)``
   Coerce supported inputs into :class:`decimal.Decimal`.
