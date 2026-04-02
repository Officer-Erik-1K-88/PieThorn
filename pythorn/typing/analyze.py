import inspect
from abc import abstractmethod
from collections.abc import Sequence
from typing import overload, Iterable, Mapping


class Argument:
    def __init__(self, parameter: inspect.Parameter):
        self._param = parameter
        self._name = self._param.name
        self._kind = self._param.kind
        self._default = self._param.default
        self._annotation = self._param.annotation

    @property
    def parameter(self):
        return self._param

    @property
    def name(self):
        return self._name

    @property
    def kind(self):
        return self._kind

    @property
    def default(self):
        return self._default

    @property
    def annotation(self):
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
            if param.kind == param.POSITIONAL_ONLY:
                pos.append(param.name)
            elif param.kind == param.POSITIONAL_OR_KEYWORD:
                pok.append(param.name)
            elif param.kind == param.KEYWORD_ONLY:
                key.append(param.name)
            elif param.kind == param.VAR_POSITIONAL:  # *args
                self._has_args = True
            elif param.kind == param.VAR_KEYWORD:  # **kwargs
                self._has_kwargs = True
        self._positional = tuple(pos)
        self._keyword = tuple(key)
        self._positional_or_keyword = tuple(pok)
        self._arg_count = len(self._positional)+len(self._positional_or_keyword)

    @property
    def positional(self):
        return tuple(self._positional)

    @property
    def keyword(self):
        return tuple(self._keyword)

    @property
    def positional_or_keyword(self):
        return tuple(self._positional_or_keyword)

    @property
    def has_args(self):
        return self._has_args

    @property
    def has_kwargs(self):
        return self._has_kwargs

    @property
    def arg_count(self):
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
        return self._object

    @property
    def arguments(self):
        return self._arguments

    @property
    def return_annotation(self):
        return self._return_annotation

    def callable(self):
        return callable(self._object)

    def awaitable(self):
        return inspect.isawaitable(self._object)

    def ismethod(self):
        return inspect.ismethod(self._object)

    def ismethoddescriptor(self):
        return inspect.ismethoddescriptor(self._object)

    def ismethodwrapper(self):
        return inspect.ismethodwrapper(self._object)

    def isfunction(self):
        return inspect.isfunction(self._object)

    def isgeneratorfunction(self):
        return inspect.isgeneratorfunction(self._object)

    def isgenerator(self):
        return inspect.isgenerator(self._object)

    def isasyncgenfunction(self):
        return inspect.isasyncgenfunction(self._object)

    def isasyncgen(self):
        return inspect.isasyncgen(self._object)

    def isclass(self):
        return inspect.isclass(self._object)

    def ismodule(self):
        return inspect.ismodule(self._object)

    def ismemberdescriptor(self):
        return inspect.ismemberdescriptor(self._object)

    def isgetsetdescriptor(self):
        return inspect.isgetsetdescriptor(self._object)

    def isdatadescriptor(self):
        return inspect.isdatadescriptor(self._object)

    def iscoroutinefunction(self):
        return inspect.iscoroutinefunction(self._object)

    def iscoroutine(self):
        return inspect.iscoroutine(self._object)

    def isroutine(self):
        return inspect.isroutine(self._object)

    def istraceback(self):
        return inspect.istraceback(self._object)

    def isframe(self):
        return inspect.isframe(self._object)

    def iscode(self):
        return inspect.iscode(self._object)

    def isbuiltin(self):
        return inspect.isbuiltin(self._object)

    def isabstract(self):
        return inspect.isabstract(self._object)


def analyze(obj):
    """
    This function will analyze the provided object.

    :param obj: The object to analyze.
    :return: The information on the object.
    """
    return Info(obj)