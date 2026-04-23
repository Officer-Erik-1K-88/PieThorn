Building The Docs
=================

The documentation sources live directly in the ``docs/`` directory and are
structured for Sphinx.

Sphinx Configuration
--------------------

The Sphinx configuration file is ``docs/conf.py``.

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

   git tag -a v0.1.0 -m "PieThorn 0.1.0"

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

GitHub Actions Publishing
-------------------------

The repository includes package publishing workflows under
``.github/workflows/`` and a GitHub Pages workflow at
``.github/workflows/docs-pages.yml``.

Behavior:

* pushing a tag such as ``v0.1.1`` builds the ``piethorn`` distribution and
  publishes it to PyPI
* successful PyPI publishes also create or update the matching GitHub Release
  and attach the built distribution files
* manually running the workflow can publish the selected ref to TestPyPI or
  PyPI

The package workflows use ``setuptools-scm``, so they check out the full Git
history and tags before building.

Versioned GitHub Pages
======================

The docs site is published from Git tags so each release keeps its own URL.

Behavior
--------

* pushing a ``vX.Y.Z`` tag runs ``.github/workflows/docs-pages.yml``
* the workflow rebuilds the full docs site for all matching tags
* each tag is published at ``/<tag>/``
* the site root redirects to the latest tag
* a version selector in the Sphinx sidebar lets readers switch between tags

Deduplication
-------------

The workflow hashes the documentation inputs for each tag:

* ``docs/``
* ``piethorn/``
* ``README.rst``
* ``pyproject.toml``
* ``setup.py``
* ``requirements.txt``

If two tags produce the same hash, the workflow builds that documentation tree
once under ``_builds/<hash>/`` and publishes the tag paths as symbolic links to
that shared build. This keeps version navigation intact without rebuilding or
storing duplicate output for unchanged documentation versions.

PyPI configuration
------------------

The publishing workflows are designed for trusted publishing rather than
long-lived API tokens.

Configure PyPI and TestPyPI to trust the matching workflow file in this
repository:

* owner: ``Officer-Erik-1K-88``
* repository: ``PieThorn``
* workflow: ``.github/workflows/live-publish.yml`` with environment ``pypi``
* workflow: ``.github/workflows/test-publish.yml`` with environment ``testpypi``

After that setup:

* create and push a ``vX.Y.Z`` tag to run ``live-publish.yml`` and publish to
  PyPI
* create and push a ``vX.Y.Z-test`` tag to run ``test-publish.yml`` and
  publish to TestPyPI
* use the ``test-publish.yml`` manual workflow dispatch to dry-run a build
  against TestPyPI for any selected ref
* use the ``live-publish.yml`` manual workflow dispatch to publish a selected
  ref to PyPI, and set ``gitrelease`` if you also want the matching GitHub
  Release created after the PyPI publish succeeds
