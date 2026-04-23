import inspect
from abc import abstractmethod
from collections.abc import Sequence
from typing import overload, Iterable, Mapping


class Argument:
    """Wrap ``inspect.Parameter`` with stable comparison-friendly accessors."""

    def __init__(self, parameter: inspect.Parameter):
        self._param = parameter
        self._name = self._param.name
        self._kind = self._param.kind
        self._default = self._param.default
        self._annotation = self._param.annotation

    @property
    def parameter(self):
        """Return the wrapped ``inspect.Parameter``."""
        return self._param

    @property
    def name(self):
        """Return the parameter name."""
        return self._name

    @property
    def kind(self):
        """Return the parameter kind."""
        return self._kind

    @property
    def default(self):
        """Return the parameter default value."""
        return self._default

    @property
    def annotation(self):
        """Return the parameter annotation."""
        return self._annotation

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<{} "{}">'.format(self.__class__.__name__, self.parameter)

    def __hash__(self):
        return hash((self._name, self._kind, self._annotation, self._default))

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, (Argument, inspect.Parameter)):
            return False
        return (self.name == other.name and
                self.kind == other.kind and
                self.default == other.default and
                self.annotation == other.annotation)


class Arguments(Sequence[Argument]):
    """Provide a sequence view over analyzed callable parameters."""

    def __new__(cls, iterable: Iterable[Argument | inspect.Parameter] = None):
        if isinstance(iterable, Arguments):
            return iterable
        instance = super().__new__(cls)
        return instance

    def __init__(self, seg):
        if isinstance(seg, Mapping):
            par = seg.values()
        else:
            par = seg
        self._params = []
        pos = []
        key = []
        pok = []
        self._has_args = False
        self._has_kwargs = False
        for param in par:
            if isinstance(param, inspect.Parameter):
                parameter = Argument(param)
            elif isinstance(param, Argument):
                parameter = param
            else:
                raise TypeError("The given type in the iterable isn't correct, must be inspect.Parameter or Argument.")
            self._params.append(parameter)
            if parameter.kind == inspect.Parameter.POSITIONAL_ONLY:
                pos.append(parameter.name)
            elif parameter.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                pok.append(parameter.name)
            elif parameter.kind == inspect.Parameter.KEYWORD_ONLY:
                key.append(parameter.name)
            elif parameter.kind == inspect.Parameter.VAR_POSITIONAL:  # *args
                self._has_args = True
            elif parameter.kind == inspect.Parameter.VAR_KEYWORD:  # **kwargs
                self._has_kwargs = True
        self._positional = tuple(pos)
        self._keyword = tuple(key)
        self._positional_or_keyword = tuple(pok)
        self._arg_count = len(self._positional)+len(self._positional_or_keyword)

    @property
    def positional(self):
        """Return names of positional-only parameters."""
        return tuple(self._positional)

    @property
    def keyword(self):
        """Return names of keyword-only parameters."""
        return tuple(self._keyword)

    @property
    def positional_or_keyword(self):
        """Return names of parameters that accept positional or keyword binding."""
        return tuple(self._positional_or_keyword)

    @property
    def has_args(self):
        """Return whether ``*args`` is present."""
        return self._has_args

    @property
    def has_kwargs(self):
        """Return whether ``**kwargs`` is present."""
        return self._has_kwargs

    @property
    def arg_count(self):
        """Return the number of non-variadic positional parameters."""
        return self._arg_count

    @overload
    def __getitem__(self, index: int):
        return self._params[index]

    @overload
    def __getitem__(self, index: slice) -> Sequence[Argument]:
        section = self._params[index]
        return Arguments(section)

    def __getitem__(self, index):
        if isinstance(index, int):
            return self._params[index]
        elif isinstance(index, slice):
            section = self._params[index]
            return Arguments(section)
        raise KeyError("index not of correct type, must be an int or slice.")

    def __len__(self):
        return len(self._params)


class Info:
    """Collect inspection metadata and predicates for an arbitrary object."""

    def __init__(self, obj):
        self._object = obj
        self._signature = None
        self._arguments = None
        self._return_annotation = None
        if self.callable():
            self._signature = inspect.signature(self._object)
            self._arguments = Arguments(self._signature.parameters)
            self._return_annotation = self._signature.return_annotation

    @property
    def object(self):
        """Return the inspected object."""
        return self._object

    @property
    def arguments(self):
        """Return analyzed callable arguments when the object is callable."""
        return self._arguments

    @property
    def return_annotation(self):
        """Return the callable's declared return annotation when available."""
        return self._return_annotation

    def callable(self):
        """Return whether the inspected object is callable."""
        return callable(self._object)

    def awaitable(self):
        """Return whether the inspected object is awaitable."""
        return inspect.isawaitable(self._object)

    def ismethod(self):
        """Return whether the inspected object is a bound method."""
        return inspect.ismethod(self._object)

    def ismethoddescriptor(self):
        """Return whether the inspected object is a method descriptor."""
        return inspect.ismethoddescriptor(self._object)

    def ismethodwrapper(self):
        """Return whether the inspected object is a method-wrapper instance."""
        return inspect.ismethodwrapper(self._object)

    def isfunction(self):
        """Return whether the inspected object is a Python function."""
        return inspect.isfunction(self._object)

    def isgeneratorfunction(self):
        """Return whether the inspected object is a generator function."""
        return inspect.isgeneratorfunction(self._object)

    def isgenerator(self):
        """Return whether the inspected object is a generator iterator."""
        return inspect.isgenerator(self._object)

    def isasyncgenfunction(self):
        """Return whether the inspected object is an async generator function."""
        return inspect.isasyncgenfunction(self._object)

    def isasyncgen(self):
        """Return whether the inspected object is an async generator iterator."""
        return inspect.isasyncgen(self._object)

    def isclass(self):
        """Return whether the inspected object is a class."""
        return inspect.isclass(self._object)

    def ismodule(self):
        """Return whether the inspected object is a module."""
        return inspect.ismodule(self._object)

    def ismemberdescriptor(self):
        """Return whether the inspected object is a member descriptor."""
        return inspect.ismemberdescriptor(self._object)

    def isgetsetdescriptor(self):
        """Return whether the inspected object is a get-set descriptor."""
        return inspect.isgetsetdescriptor(self._object)

    def isdatadescriptor(self):
        """Return whether the inspected object is a data descriptor."""
        return inspect.isdatadescriptor(self._object)

    def iscoroutinefunction(self):
        """Return whether the inspected object is a coroutine function."""
        return inspect.iscoroutinefunction(self._object)

    def iscoroutine(self):
        """Return whether the inspected object is a coroutine object."""
        return inspect.iscoroutine(self._object)

    def isroutine(self):
        """Return whether the inspected object is any routine-like callable."""
        return inspect.isroutine(self._object)

    def istraceback(self):
        """Return whether the inspected object is a traceback."""
        return inspect.istraceback(self._object)

    def isframe(self):
        """Return whether the inspected object is a frame."""
        return inspect.isframe(self._object)

    def iscode(self):
        """Return whether the inspected object is a code object."""
        return inspect.iscode(self._object)

    def isbuiltin(self):
        """Return whether the inspected object is a built-in function or method."""
        return inspect.isbuiltin(self._object)

    def isabstract(self):
        """Return whether the inspected object is abstract."""
        return inspect.isabstract(self._object)


def analyze(obj):
    """
    This function will analyze the provided object.

    :param obj: The object to analyze.
    :return: The information on the object.
    """
    return Info(obj)
