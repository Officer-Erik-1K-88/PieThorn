JSONEncoder Class
=================

.. py:class:: JSONEncoder(...)

Purpose
-------

``JSONEncoder`` customizes JSON formatting so primitive collections can remain
compact while nested complex structures can still be rendered with indentation.

Important methods
-----------------

``dumps(obj)``
   Return the encoded JSON string.

``iterencode(obj)``
   Yield the encoded JSON chunks using the custom formatting rules.
