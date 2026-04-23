PieThorn Documentation
=====================

PieThorn is a utility library that groups together several reusable Python
helpers:

* collection primitives such as character wrappers, mapping helpers, and
  read-only sequence views
* file and import helpers for working with project-local paths and modules
* lightweight logging and progress counters
* math utilities including word/number conversion, equation parsing, and
  boolean gate helpers
* callable and argument inspection helpers

This documentation is organized as a manual first and a detailed API reference
second. The reference pages intentionally mix narrative explanation with Sphinx
directives so they can be read directly as source files and also rendered into a
full documentation site.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: Guides

   guides/index

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/index

.. toctree::
   :maxdepth: 1
   :caption: Documentation Infrastructure

   building

Highlights
----------

``piethorn.collections``
   Character-oriented data structures, an ordered mutable mapping, slice
   composition helpers, and immutable views over sequences and mappings.

``piethorn.filehandle``
   Filesystem wrappers for creating and editing files, plus helpers for
   resolving import paths relative to a detected project root.

``piethorn.logging``
   A simple logger with counter objects that can track progress and optionally
   emit messages through the logger.

``piethorn.math``
   Boolean gate utilities, skewed random generation, numeric word conversion,
   timing formatters, and a decimal-based equation parser/evaluator.

``piethorn.typing``
   Utilities for describing runtime arguments and inspecting callable
   signatures in a structured way.

Project Status
--------------

The project metadata currently marks PieThorn as alpha-quality software. The
test suite is the most reliable source for expected behavior, and the guides in
this documentation are based on the package implementation and those tests.

Documentation Scope
-------------------

The API reference aims to cover the project-defined functions, classes, and
methods with:

* expected purpose
* key behavior notes
* example usage
* links to the autodoc-generated member listings
