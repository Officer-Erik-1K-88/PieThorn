Quickstart
==========

Collections
-----------

PieThorn includes a few collection helpers that wrap low-level Python patterns:

.. code-block:: python

   from piethorn.collections.char import CharSequence
   from piethorn.collections.mapping import Map
   from piethorn.collections.views import SequenceView

   text = CharSequence(["ab", " ", "C"])
   mapping = Map(["left", "right"], [1, 2])
   view = SequenceView([1, 2, 3, 4], reverse=True, cut=slice(1, 4))

   assert str(text) == "ab C"
   assert mapping["left"] == 1
   assert list(view) == [4, 3, 2]

Equation Evaluation
-------------------

The equation engine parses expressions into reusable token trees and evaluates
them with :class:`decimal.Decimal` semantics:

.. code-block:: python

   from decimal import Context
   from piethorn.math.equation import Equation

   ctx = Context()
   eq = Equation("$value$ + $fallback:2$", ctx)

   assert eq.calculate({"value": 3}) == 5

Logging And Progress
--------------------

The logging package combines output helpers with counters:

.. code-block:: python

   from piethorn.logging.logger import Logger

   logger = Logger(debug_level=1)
   logger.info("starting")

   counter = logger.count("jobs", step=0.5)
   counter.add(2)
   counter.tick()

File Utilities
--------------

The file wrapper can build paths relative to a root object:

.. code-block:: python

   from piethorn.filehandle.filehandling import File

   root = File("tmp_project", find_children=False)
   child = root.create_child("data/example.txt", "hello")
   child.write("second line")

Typing Utilities
----------------

Use ``piethorn.typing.argument`` when you need a runtime container for typed
arguments, and ``piethorn.typing.analyze`` when you need structured data from
``inspect.signature``:

.. code-block:: python

   from piethorn.typing.analyze import analyze

   def sample(a, /, b: int, *args, c=3, **kwargs) -> str:
       return "ok"

   info = analyze(sample)
   assert info.arguments.positional == ("a",)
   assert info.arguments.keyword == ("c",)
