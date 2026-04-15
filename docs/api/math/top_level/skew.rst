skew Function
=============

.. py:function:: skew(skew_at=0.6, weight=0.9, minimum=0, maximum=100, is_int=False)

Purpose
-------

Generate a bounded random value that is biased toward a target point.

Important parameters
--------------------

``skew_at``
   Normalized target point in the range 0 to 1.

``weight``
   Strength of the skew bias.

``minimum`` / ``maximum``
   Output bounds.

``is_int``
   Whether to round the output to an integer.
