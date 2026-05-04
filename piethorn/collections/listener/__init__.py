"""
Event listener framework for attaching callbacks to method calls.

This package exposes the listener primitives, decorators, and sequence base
classes used to trigger named events from ``Listenable`` objects.
"""

from __future__ import annotations

from abc import abstractmethod, ABC
from typing import Iterable, MutableSequence, Sequence

from piethorn.collections.listener.event import Event, EventBuilder, EventEnd, DEFAULT_EVENT_BUILDER
from piethorn.collections.listener.listener import Listener, ListenerBuilder, GetListenerError
from piethorn.collections.listener.listens import listens
from piethorn.collections.listener.listenable import Listenable, ListenerHolder, GLOBAL_LISTENERS
from piethorn.collections.listener.sequence import ListenerSequence, MutableListenerSequence

__all__ = [
    # Event stuff
    "Event",
    "EventBuilder",
    "DEFAULT_EVENT_BUILDER",
    "EventEnd",
    # Listener stuff
    "GetListenerError",
    "Listener",
    "ListenerBuilder",
    # Listenable stuff
    "Listenable",
    "ListenerHolder",
    "GLOBAL_LISTENERS",
    # Decorators
    "listens",
    # Abstract Classes
    "ListenerSequence",
    "MutableListenerSequence",
]
