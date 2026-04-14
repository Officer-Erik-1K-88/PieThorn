from typing import Iterable, Dict, Mapping

from ._consonant import Consonants, Consonant


class NumPrefix:
    """Represent a named numeric prefix used in word conversion."""

    def __init__(
            self,
            num: int,
            prefix: str,
            convert: str,
            consonants: Iterable[Consonant],
    ):
        """
        Defines a part of a number word.

        :param num: The number that the prefix represents
        :param prefix: The prefix being represented
        :param convert: The second prefix that can be used. Defaults to ``prefix``
        :param consonants: The optional suffixes to this prefix. This is also used to check if the previous ``NumberPrefix`` should use one of its consonants.
        """
        self._num = num
        self._prefix = prefix
        self._convert = convert
        self._consonants = Consonants(consonants)

    @property
    def place(self):
        """ The digits place that this prefix is in """
        if self._num < 10:
            return "units"
        elif self._num < 100:
            return "tens"
        elif self._num < 1000:
            return "hundreds"
        elif self._num < 10000:
            return "thousands"
        else:
            return "unknown"

    @property
    def prefix(self):
        """ The actual prefix that this prefix is """
        return self._prefix

    @property
    def convert(self):
        """ A second prefix that this prefix can be """
        if self._convert is None or self._convert == "":
            return self._prefix
        return self._convert

    @property
    def num(self):
        """ The number this prefix represents """
        return self._num

    @property
    def consonants(self):
        """
        The consonants that this prefix uses.

        Refer to ``Consonant`` class for details on how consonants work.
        """
        return self._consonants


class NumPrefixDict(Mapping[int, NumPrefix]):
    """
    Maps out a set of ``NumPrefix`` classes.
    """
    def __init__(self, *args: NumPrefix):
        self._prefixes: Dict[int, NumPrefix] = {}
        self._places: set[str] = set()
        if len(args) != 0:
            self._add_all(args)

    def __len__(self):
        return len(self._prefixes)

    def __iter__(self):
        return iter(self._prefixes)

    def __getitem__(self, item):
        return self._prefixes[item]

    @property
    def place_count(self):
        """Return how many distinct digit places are represented."""
        return len(self._places)

    def has_place(self, place: str):
        """Return whether any prefix exists for the given digit place."""
        return place in self._places

    def _add(self, prefix: NumPrefix):
        index = prefix.num
        self._places.add(prefix.place)
        self._prefixes[index] = prefix

    def _add_all(self, prefixes: Iterable[NumPrefix]):
        for prefix in prefixes:
            self._add(prefix)
