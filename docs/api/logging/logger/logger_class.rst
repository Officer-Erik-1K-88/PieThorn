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

   .. code-block:: python

      import io

      stream = io.StringIO()
      logger.set_default_file("INFO", stream)
      logger.get_default_file("INFO")

``base_log(...)`` / ``log(...)``
   Core message emission helpers.

   .. code-block:: python

      logger.base_log("alpha", "beta")
      logger.log("INFO", "boot complete")

``error(...)``, ``warn(...)``, ``info(...)``
   Severity wrappers.

``log_sep(...)``
   Print a separator line.

   .. code-block:: python

      logger.log_sep(title="phase 1")

``count(...)`` / ``percent(...)``
   Create progress counters.

Behavior notes
--------------

The logger tracks message counts internally using ``Counter`` objects, including
``log_count``, ``errors``, ``warns``, ``infos``, and ``seps``.
