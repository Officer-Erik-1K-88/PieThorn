letter_to_number Function
=========================

.. py:function:: letter_to_number(sentence, percent_to_convert=-1.0)

Purpose
-------

Transform eligible characters in a string into digit lookalikes.

Behavior notes
--------------

* only supported characters are converted
* a negative or out-of-range percentage triggers randomized selection logic
* the conversion is non-deterministic unless the random seed is controlled
