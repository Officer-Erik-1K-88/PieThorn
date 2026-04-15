Installation
============

Requirements
------------

PyThorn targets Python 3.12 and newer.

Install From Source
-------------------

From the repository root:

.. code-block:: bash

   pip install .

For editable development installs:

.. code-block:: bash

   pip install -e .

Project Layout
--------------

The library is published as the ``pythorn`` package. The repository contains:

* ``pythorn/`` for the implementation
* ``tests/`` for the unit test suite
* ``README.rst`` for the short project summary
* ``pyproject.toml`` for build metadata

Optional Documentation Build
----------------------------

The files in ``docs/`` are written in reStructuredText and are structured to
work well with Sphinx. A minimal Sphinx configuration can point at this folder
and render the API directives used throughout the reference pages.
