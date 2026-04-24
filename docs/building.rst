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

Use annotated tags in PEP 440-compatible formats:

* ``vX.Y.ZrcN`` for TestPyPI release candidates, for example ``v0.1.1rc1``
* ``vX.Y.Z`` for final PyPI releases, for example ``v0.1.1``

Avoid suffixes like ``-test`` because they are valid Git tag names but not
valid Python package versions, so ``setuptools-scm`` cannot turn them into
publishable package metadata.

Recommended release flow
------------------------

Validate the working tree from the repository root before you tag anything:

.. code-block:: bash

   git status
   python -m pip install --upgrade build twine
   python -m build
   python -m twine check dist/*

If you want a TestPyPI release candidate first, tag and push an ``rc`` build:

.. code-block:: bash

   git tag -a v0.1.1rc1 -m "PieThorn 0.1.1 release candidate 1"
   git push origin v0.1.1rc1

After validating that release candidate on TestPyPI, create and push the final
release tag on the commit you want to publish:

.. code-block:: bash

   git tag -a v0.1.1 -m "PieThorn 0.1.1"
   git push origin main
   git push origin v0.1.1

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
* if ``info/`` exists, its contents become the GitHub Pages site root
* if ``info/`` does not exist, the workflow generates a fallback homepage
* documentation lives under ``/docs/``
* each tag is published at ``/docs/<tag>/``
* ``/docs/`` redirects to ``/docs/latest/``
* every rendered site page gets the shared top navigation bar
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
storing duplicate output for unchanged documentation versions. The ``latest``
alias is also published under ``/docs/latest/``.

Info Site Content
-----------------

The optional ``info/`` directory is treated as the non-documentation portion of
the GitHub Pages site.

Behavior:

* ``.html`` files under ``info/`` are copied to the site root and get the
  shared top navigation injected
* ``.rst`` files under ``info/`` are rendered to ``.html`` pages
* ``.txt`` files under ``info/`` are rendered as plain-text pages inside the
  shared site chrome
* ``info/index.html``, ``info/index.rst``, or ``info/index.txt`` can become
  the site homepage
* ``info/docs`` is reserved and will fail the build because ``/docs/`` is
  managed by the versioned documentation publisher
* conflicting source files such as ``info/about.rst`` and ``info/about.html``
  will fail the build because they target the same output path

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
* create and push a ``vX.Y.ZrcN`` tag to run ``test-publish.yml`` and publish
  to TestPyPI
* use the ``test-publish.yml`` manual workflow dispatch to dry-run a build
  against TestPyPI for any selected ref
* use the ``live-publish.yml`` manual workflow dispatch to publish a selected
  ref to PyPI, and set ``gitrelease`` if you also want the matching GitHub
  Release created after the PyPI publish succeeds
