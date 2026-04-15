Building The Docs
=================

The documentation sources live directly in the ``docs/`` directory and are
structured for Sphinx.

Sphinx Configuration
--------------------

The Sphinx configuration file is [conf.py](/mnt/programming/Libs/Python/PyThorn/docs/conf.py).

It currently enables:

* ``sphinx.ext.autodoc``
* ``sphinx.ext.napoleon``

Suggested build commands
------------------------

From the repository root, common approaches are:

.. code-block:: bash

   python -m sphinx -b html docs docs/_build/html

or, when ``sphinx-build`` is available on ``PATH``:

.. code-block:: bash

   sphinx-build -b html docs docs/_build/html

Notes
-----

If Sphinx was installed into a virtual environment or a different interpreter
than the shell default, use the matching Python executable for the build
command.

Packaging And Release Tags
==========================

Package builds use ``setuptools-scm`` to derive the version from Git tags.
That means releases should be cut from tagged commits instead of by editing a
hard-coded version string in the source tree.

Tag format
----------

Use annotated tags in ``vX.Y.Z`` format:

* ``v0.1.0`` for the first public release
* ``v0.1.1`` for a bugfix release
* ``v0.2.0`` for a backwards-compatible feature release
* ``v1.0.0`` when the public API is considered stable

Recommended release flow
------------------------

From the repository root:

.. code-block:: bash

   git status
   python -m pip install --upgrade build twine
   python -m build
   python -m twine check dist/*

Create the release tag on the commit you want to publish:

.. code-block:: bash

   git tag -a v0.1.0 -m "PyThorn 0.1.0"

Then verify what version ``setuptools-scm`` resolved:

.. code-block:: bash

   python -m build

If the build output looks correct, push the commit and tag:

.. code-block:: bash

   git push origin main
   git push origin v0.1.0

For a dry run, upload to TestPyPI first:

.. code-block:: bash

   python -m twine upload --repository testpypi dist/*

Then publish the same built artifacts to PyPI:

.. code-block:: bash

   python -m twine upload dist/*

Development versions
--------------------

Commits after a release tag will automatically build as development versions
derived from the most recent tag. To keep those versions meaningful, tag every
public release and avoid rewriting published tags.
