Logger Class
============

.. py:class:: Logger(debug_level=0)

Purpose
-------

``Logger`` is a lightweight message printer with severity tagging and integrated
counter factories.

Examples
--------

.. code-block:: python

   from pythorn.logging.logger import Logger

   logger = Logger(debug_level=1)
   logger.info("hello")

Methods
-------

``get_default_file(...)`` / ``set_default_file(...)``
   Control output streams.

``base_log(...)`` / ``log(...)``
   Core message emission helpers.

``error(...)``, ``warn(...)``, ``info(...)``
   Severity wrappers.

``log_sep(...)``
   Print a separator line.

``count(...)`` / ``percent(...)``
   Create progress counters.
