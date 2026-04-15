Logger Module
=============

Module: :mod:`pythorn.logging.logger`

Overview
--------

This module provides :class:`Logger`, a small output helper with built-in
message counters and factory methods for progress counters.

.. toctree::
   :maxdepth: 1

   logger/logger_class

``Logger``
----------

.. py:class:: Logger(debug_level=0)

   Simple logger that prints tagged messages and tracks message counts.

   Example
   ~~~~~~~

   .. code-block:: python

      from pythorn.logging.logger import Logger

      logger = Logger(debug_level=1)
      logger.info("hello")
      logger.warn("careful")

   Methods
   ~~~~~~~

   ``get_default_file(log_type, fallback_type="default")``
      Return the configured output stream for a log type.

   ``set_default_file(log_type, file)``
      Change or clear the configured stream for a log type.

   ``base_log(*msgs, level=0, sep=" ", end="\\n", file=None, flush=False)``
      Low-level print helper. Returns ``False`` when the active debug level is
      too low.

   ``log(title, *msgs, level=0, title_sep=" ", sep=" ", end="\\n", file=None, flush=False)``
      Log a titled message and update the general log counter.

   ``error(*msgs, **kwargs)``, ``warn(*msgs, **kwargs)``, ``info(*msgs, **kwargs)``
      Severity-specific wrappers around ``log``.

      .. code-block:: python

         logger.error("failed")
         logger.warn("careful")
         logger.info("boot complete")

   ``log_sep(size=50, title=None, *, size_is_sep_count=False, sep="-", end="\\n", file=None, flush=False)``
      Print a separator line.

   ``percent(name, current=0, cap=100, step=1)`` and ``count(name, step=1)``
      Factory helpers for :class:`pythorn.logging.counter.Percent` and
      :class:`pythorn.logging.counter.Counter`.

Autodoc
-------

.. automodule:: pythorn.logging.logger
   :members:
   :undoc-members:
