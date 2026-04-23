PieThorn
=======

PieThorn is a Python utility library that collects several small but reusable
tools under one package. It currently includes:

* collection helpers such as character wrappers, ordered mappings, slice
  composition utilities, and read-only views
* filesystem and import helpers for path-aware file handling and module loading
* lightweight logging and progress counters
* math helpers for boolean gates, skewed random generation, number-word
  conversion, timing utilities, and decimal-based equation parsing
* runtime argument and callable inspection helpers

Project Status
--------------

PieThorn is currently marked as alpha-quality software. The public behavior
described here is based on the current implementation and test suite.

Requirements
------------

* Python 3.12 or newer

Installation
------------

Install from PyPI with:

.. code-block:: bash

   pip install piethorn

To install from a local checkout, first change into the repository root (the
directory that contains ``pyproject.toml``), then run:

.. code-block:: bash

   cd /path/to/PieThorn
   pip install .

This installs the package from your working tree as a normal, non-editable
installation.

For development work in the same checkout, use an editable install instead:

.. code-block:: bash

   cd /path/to/PieThorn
   pip install -e .

Editable mode keeps the installed package linked to the repository, so changes
you make under ``piethorn/`` are picked up without reinstalling after each edit.

Package Overview
----------------

``piethorn.collections``
   Character-oriented types, ordered mappings, slice-composition helpers, and
   immutable views over existing sequences and mappings.

``piethorn.filehandle``
   Filesystem wrappers for building and editing files, JSON persistence helpers,
   and importer utilities for project-relative path and module resolution.

``piethorn.logging``
   A simple logger plus counter types for progress reporting and parent-child
   percentage tracking.

``piethorn.math``
   Logic gate helpers, skewed random values, numeric word conversion, timing
   formatting, and an equation parser/evaluator based on ``decimal.Decimal``.

``piethorn.typing``
   Runtime argument-definition containers and ``inspect``-based callable
   analysis helpers.

Quick Examples
--------------

Collections
~~~~~~~~~~~

.. code-block:: python

   from piethorn.collections.char import CharSequence
   from piethorn.collections.mapping import Map
   from piethorn.collections.views import SequenceView

   sequence = CharSequence(["ab", " ", "C"])
   mapping = Map(["left", "right"], [1, 2])
   view = SequenceView([1, 2, 3, 4], reverse=True, cut=slice(1, 4))

   assert str(sequence) == "ab C"
   assert mapping["left"] == 1
   assert list(view) == [4, 3, 2]

Equation Evaluation
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from decimal import Context
   from piethorn.math.equation import Equation

   eq = Equation("$value$ + $fallback:2$", Context())
   assert eq.calculate({"value": 3}) == 5

Logging And Progress
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from piethorn.logging.logger import Logger

   logger = Logger(debug_level=1)
   logger.info("starting")

   counter = logger.count("jobs", step=0.5)
   counter.add(2)
   counter.tick()

File Utilities
~~~~~~~~~~~~~~

.. code-block:: python

   from piethorn.filehandle.filehandling import File

   root = File("tmp_project", find_children=False)
   child = root.create_child("data/example.txt", "hello")
   child.write("second line")

Typing Utilities
~~~~~~~~~~~~~~~~

.. code-block:: python

   from piethorn.typing.analyze import analyze

   def sample(a, /, b: int, *args, c=3, **kwargs) -> str:
       return "ok"

   info = analyze(sample)
   assert info.arguments.positional == ("a",)
   assert info.arguments.keyword == ("c",)

Documentation
-------------

The full documentation source lives in ``docs/`` and includes:

* getting-started pages
* narrative guides for each subsystem
* a layered API reference split into package, module, class, and function pages

If Sphinx is available in your environment, a typical HTML build looks like:

.. code-block:: bash

   python -m sphinx -b html docs docs/_build/html

Repository Layout
-----------------

* ``piethorn/`` contains the package implementation
* ``tests/`` contains the unit tests
* ``docs/`` contains the reStructuredText documentation tree
* ``pyproject.toml`` defines the build metadata

Why PieThorn
-----------

PieThorn is useful when you want a small grab-bag library of utilities that are
more structured than ad-hoc snippets but lighter than pulling in many separate
packages for simple tasks.
