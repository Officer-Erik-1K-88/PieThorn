from typing import Iterable, AbstractSet


class Consonant:
    def __init__(self, converts: str, trails: bool, to: str=None):
        """
        This is the suffix of a ``NumberPrefix``.
        It helps add depth and variety to number words.

        :param converts: The consonant that this class represents
        :param trails: Whether this consonant is appended to the end of a ``NumberPrefix`` or if it decides the consonant of the previous ``NumberPrefix``
        :param to: The consonant that is appended to the end of a ``NumberPrefix``. Defaults to ``converts``.
        """
        self._converts = converts
        self._trails = trails
        self._to = to

    @property
    def converts(self):
        """ The consonant that this class represents """
        return self._converts

    @property
    def trails(self):
        """
        If ``True``, then this defines that the ``NumberPrefix`` gains this consonant
        when placed before a ``NumberPrefix`` that defines the same consonant.
        While, if ``False``, then this defines that the ``NumberPrefix`` tells the previous
        ``NumberPrefix`` should gain this consonant if it defines the same consonant and
        has ``trails`` set to ``True``.
        """
        return self._trails

    @property
    def to(self):
        """ The actual consonant that is appended to the end of a ``NumberPrefix`` """
        if self._to is None:
            return self._converts
        return self._to

    def __eq__(self, other):
        if isinstance(other, Consonant):
            return self._converts == other._converts
        elif isinstance(other, str):
            return self._converts == other
        return False


class Consonants(AbstractSet[Consonant]):
    """
    A Set of ``Consonant`` classes.
    """
    def __init__(self, consonants: Iterable[Consonant]):
        self._consonants = {}
        self._length = 0
        for consonant in consonants:
            if consonant.converts not in self._consonants:
                self._consonants[consonant.converts] = consonant
                self._length += 1

    def __len__(self):
        return self._length

    def __iter__(self):
        for conv in self._consonants:
            yield self._consonants[conv]

    def __contains__(self, x):
        if isinstance(x, Consonant):
            check_for = x.converts
        else:
            check_for = x
        return check_for in self._consonants
