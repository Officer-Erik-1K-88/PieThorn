Analyze Module
==============

Module: :mod:`piethorn.typing.analyze`

Overview
--------

This module wraps ``inspect`` with stable helper objects for examining callables
and other Python objects.

.. toctree::
   :maxdepth: 1

   analyze/analyze_argument
   analyze/analyze_arguments
   analyze/info_class
   analyze/analyze_function

``Argument``
------------

.. py:class:: Argument(parameter)

   Wrapper around ``inspect.Parameter`` with stable properties:

   * ``parameter``
   * ``name``
   * ``kind``
   * ``default``
   * ``annotation``

``Arguments``
-------------

.. py:class:: Arguments(iterable=None)

   Sequence wrapper over analyzed parameters.

   Important properties:

   * ``positional``
   * ``keyword``
   * ``positional_or_keyword``
   * ``has_args``
   * ``has_kwargs``
   * ``arg_count``

``Info``
--------

.. py:class:: Info(obj)

   Inspection wrapper for an arbitrary Python object.

   Important properties:

   * ``object``
   * ``arguments``
   * ``return_annotation``

   Inspection predicates
   ~~~~~~~~~~~~~~~~~~~~~

   ``callable()``, ``awaitable()``, ``ismethod()``, ``ismethoddescriptor()``,
   ``ismethodwrapper()``, ``isfunction()``, ``isgeneratorfunction()``,
   ``isgenerator()``, ``isasyncgenfunction()``, ``isasyncgen()``, ``isclass()``,
   ``ismodule()``, ``ismemberdescriptor()``, ``isgetsetdescriptor()``,
   ``isdatadescriptor()``, ``iscoroutinefunction()``, ``iscoroutine()``,
   ``isroutine()``, ``istraceback()``, ``isframe()``, ``iscode()``,
   ``isbuiltin()``, ``isabstract()``

``analyze``
-----------

.. py:function:: analyze(obj)

   Convenience entry point returning :class:`Info`.

   Example
   ~~~~~~~

   .. code-block:: python

      from piethorn.typing.analyze import analyze

      def sample(a, /, b: int, *args, c=3, **kwargs) -> str:
          return "ok"

      info = analyze(sample)
      info.arguments.positional            # ("a",)
      info.arguments.positional_or_keyword # ("b",)
      info.arguments.keyword               # ("c",)

Autodoc
-------

.. automodule:: piethorn.typing.analyze
   :members:
   :undoc-members:
