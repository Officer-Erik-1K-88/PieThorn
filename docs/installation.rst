Installation
============

Requirements
------------

PieThorn targets Python 3.12 and newer.

Install From PyPI
-----------------

Install the published distribution with:

.. code-block:: bash

   pip install piethorn

Install From Source
-------------------

To install PieThorn from a local clone, run the command from the repository root
so ``pip`` can read the local ``pyproject.toml``:

.. code-block:: bash

   cd /path/to/PieThorn
   pip install .

This creates a regular installation from the local source tree.

For local development, use an editable install from that same repository root:

.. code-block:: bash

   cd /path/to/PieThorn
   pip install -e .

Editable installs are intended for development work. The installed package
points at your checkout, so changes under ``piethorn/`` are available without
running ``pip install`` again after each edit.

Project Layout
--------------

The library is published on package indexes as ``piethorn`` while keeping the
import package name ``piethorn``. The repository contains:

* ``piethorn/`` for the implementation
* ``tests/`` for the unit test suite
* ``README.rst`` for the short project summary
* ``pyproject.toml`` for build metadata

Optional Documentation Build
----------------------------

The files in ``docs/`` are written in reStructuredText and are structured to
work well with Sphinx. A minimal Sphinx configuration can point at this folder
and render the API directives used throughout the reference pages.
