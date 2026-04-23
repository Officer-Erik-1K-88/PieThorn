import sys
from dataclasses import dataclass
from typing import Mapping, MutableSequence, Optional, Sequence, MutableMapping, Any


@dataclass(frozen=True)
class Pair[KT, VT]:
    """
    Lightweight (key, value) holder used to keep key->value pairs.
    """
    key: KT
    value: VT

class Map[KT, VT](MutableMapping[KT, VT]):
    """
    A Map is like a dictionary, but allows for any value type as a key.
    """
    def __init__(self, keys: Optional[Sequence[KT]]=None, values: Optional[Sequence[VT]]=None, *, loop_fill=False):
        """
        Creates a new Map object.

        A Map is like a dictionary, but allows for any value type as a key.

        :param keys: The keys to insert into the map.
        :param values: The values to insert into the map. Must be the same length as keys.
        :param loop_fill: Whether to fill the key/value pairs under a new list
                        or only fill if keys or values are not a `MutableSequence`. Defaults to False.
        """
        self._keys: MutableSequence[KT] = []
        self._values: MutableSequence[VT] = []
        keys_none = keys is None
        values_none = values is None
        if (keys_none and not values_none) or (values_none and not keys_none):
            raise ValueError("Both keys and values must be None or a sequence")
        if not(keys_none and values_none):
            if len(keys) != len(values):
                raise ValueError("Both keys and values must have same length")
        loop_kv = loop_fill
        if not loop_kv:
            if not keys_none:
                if isinstance(keys, MutableSequence):
                    self._keys = keys
                else:
                    loop_kv = True
            if not values_none:
                if isinstance(values, MutableSequence):
                    self._values = values
                else:
                    loop_kv = True
        if loop_kv and not keys_none:
            fill_keys = len(self._keys) == 0
            fill_values = len(self._values) == 0
            if fill_keys or fill_values:
                for i in range(len(keys)):
                    if fill_keys:
                        self._keys.append(keys[i])
                    if fill_values:
                        self._values.append(values[i])

    def __len__(self):
        return len(self._keys)

    def has_key(self, key):
        """Return whether ``key`` exists in the map."""
        return key in self._keys

    def has_value(self, key):
        """Return whether a value equal to ``key`` exists in the map."""
        return key in self._values

    def __contains__(self, key: KT) -> bool:
        return self.has_key(key)

    def __eq__(self, other):
        if not isinstance(other, Mapping):
            return NotImplemented
        if len(self) != len(other):
            return False
        for key in self._keys:
            try:
                if other[key] != self[key]:
                    return False
            except KeyError:
                return False
        return True

    def key_index(self, key, start=0, stop=sys.maxsize):
        """Return the index of ``key`` in insertion order."""
        return self._keys.index(key, start, stop)

    def value_index(self, value, start=0, stop=sys.maxsize):
        """Return the index of ``value`` in insertion order."""
        return self._values.index(value, start, stop)

    def key_at_index(self, index):
        """Return the key stored at ``index``."""
        return self._keys[index]

    def value_at_index(self, index):
        """Return the value stored at ``index``."""
        return self._values[index]

    def __getitem__(self, key, /):
        try:
            return self._values[self.key_index(key)]
        except ValueError:
            raise KeyError(key) from None

    def __setitem__(self, key, value, /):
        if self.has_key(key):
            self._values[self.key_index(key)] = value
        else:
            self._keys.append(key)
            self._values.append(value)

    def __delitem__(self, key, /):
        try:
            index = self.key_index(key)
        except ValueError:
            raise KeyError(key) from None
        del self._values[index]
        del self._keys[index]

    def __iter__(self):
        for key in self._keys:
            yield key

    def __reversed__(self):
        for key in reversed(self._keys):
            yield key
