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
