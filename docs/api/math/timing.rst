Timing Module
=============

Module: :mod:`piethorn.math.converter.timing`

Overview
--------

This module formats durations and converts supported time inputs into the
package's UTC string representation.

.. toctree::
   :maxdepth: 1

   timing/format_time
   timing/convert_seconds
   timing/convert_to_utc

``format_time``
---------------

.. py:function:: format_time(years, months, days, hours, minutes, seconds, milliseconds=0, microseconds=0, nanoseconds=0.0, time_zone="UTC")

   Format pre-separated time fields into a custom string.

   .. code-block:: python

      from piethorn.math.converter.timing import format_time

      format_time(2024, 1, 2, 3, 4, 5, 6, 7, 8, "UTC")

``convert_seconds``
-------------------

.. py:function:: convert_seconds(x, formatted=False, f_nano=True, f_micro=True, f_milli=True)

   Break seconds into years, months, days, hours, minutes, seconds, and
   fractional parts.

   When ``formatted=False``, a dictionary is returned. When ``formatted=True``,
   the result is formatted through :func:`format_time`.

``convert_to_utc``
------------------

.. py:function:: convert_to_utc(time_input, tpe="sec", formatting="%Y-%m-%d %H:%M:%S.%f")

   Convert numeric, ``datetime``, or string inputs into the UTC output format
   used by this package.

Autodoc
-------

.. automodule:: piethorn.math.converter.timing
   :members:
   :undoc-members:
