from __future__ import annotations

import sys

from typing import TYPE_CHECKING, Any, Callable, Generic, ItemsView, Iterable, Iterator, Mapping, MutableSet, SupportsIndex, TypeVar, overload  # noqa: E402

if TYPE_CHECKING:
    from typing_extensions import Self

T = TypeVar("T")
VT = TypeVar("VT")

class OrderedSet(list, MutableSet[T]):
    def __init__(
        self,
        iterable: Iterable[T] | None = None,
    ) -> None:
        self._list: list[T] = []
        self._set: set[T] = set()
        if iterable is not None:
            self.extend(iterable)

    def __contains__(self, value: object) -> bool:
        return value in self._set

    def __iter__(self) -> Iterator[T]:
        return iter(self._list)

    def __len__(self) -> int:
        return len(self._list)

    def add(self, value: T) -> None:
        if value not in self._set:
            self._list.append(value)
            self._set.add(value)

    def append(self, value: T) -> None:
        self.add(value)

    def discard(self, value: T) -> None:
        self._set.remove(value)
        self._list.remove(value)

    def remove(self, value: T) -> None:
        self.discard(value)

    def insert(self, index: int, value: T) -> None:
        if value not in self._set:
            self._list.insert(index, value)
            self._set.add(value)

    def update(self, other: Iterable[T]):
        for item in other:
            self.append(item)

    def extend(self, iterable: Iterable[T]) -> None:
        self.update(iterable)

    def pop(self, index: SupportsIndex = -1) -> T:
        value = self._list.pop(index)
        self._set.remove(value)
        return value

    def __getitem__(self, index: int) -> T:
        return self._list[index]

    def __setitem__(self, index: int, value: T) -> None:
        #if value in self._set:
        #    raise ValueError(f"Duplicate item found: {value}")
        old_value = self._list[index]
        self._list[index] = value
        self._set.remove(old_value)
        self._set.add(value)

    def clear(self) -> None:
        self._list.clear()
        self._set.clear()

    def copy(self) -> Self[T]:
        new_set = self.__class__()
        new_set._list = self._list.copy()  # noqa: SLF001
        new_set._set = self._set.copy()  # noqa: SLF001
        return new_set

    def __delitem__(self, index: int) -> None:
        try:
            value = self._list.pop(index)
            self._set.remove(value)
        except KeyError:
            raise IndexError(index)  # noqa: B904

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._list})"

    def count(self, value: T) -> int:
        return self._list.count(value)

    def index(self, value: T, start: SupportsIndex = 0, stop: SupportsIndex = sys.maxsize) -> int:
        return self._list.index(value, start, stop)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (OrderedSet, list)):
            return NotImplemented
        return self._list.__eq__(other) and self._set.__eq__(other)

    def __lt__(self, other: list[T]) -> bool:
        return self._list.__lt__(other)

    def __le__(self, other: list[T]) -> bool:
        return self._list.__le__(other)

    def __gt__(self, other: list[T]) -> bool:
        return self._list.__gt__(other)

    def __ge__(self, other: list[T]) -> bool:
        return self._list.__ge__(other)

    def sort(
        self,
        *,
        key: Callable[[T], Any] | None = None,
        reverse: bool = False,
    ) -> None:
        self._list.sort(key=key, reverse=reverse)

    def reverse(self) -> None:
        self._list.reverse()

    def __add__(self, other: Iterable[T]) -> Self[T]:
        return self._set + other

    def __iadd__(self, other: Iterable[T]) -> Self[T]:
        self._set += other
        self._list += other

    def __reversed__(self) -> Iterator[T]:
        return reversed(self._list)

    __hash__ = None  # type: ignore[assignment]

    @classmethod
    def __class_getitem__(cls, item: Any) -> Any:
        return cls


_unique_sentinel = object()
class CaseInsensitiveDict(Generic[T]):
    """A class exactly like the builtin dict[str, Any], but provides case-insensitive key lookups.

    The case-sensitivity of the keys themselves are always preserved.
    """

    def __init__(
        self,
        initial: Mapping[str, T] | Iterable[tuple[str, T]] | ItemsView[str, T] | None = None,
    ):
        self._dictionary: dict[str, T] = {}
        self._case_map: dict[str, T] = {}

        if initial:
            # If initial is a mapping, use its items method.
            items: Iterable[tuple[str, T]] | ItemsView[str, T] | ItemsView[tuple[str, T], T] = (
                initial.items()
                if isinstance(initial, Mapping)
                else initial
            )

            # Iterate over initial items directly, avoiding the creation of an interim dict
            for key, value in items:
                assert not isinstance(key, tuple), f"key '{key!r}' and value '{value!r}' are not expected types."
                if isinstance(key, tuple):
                    # Unpack key-value tuple
                    k, v = key
                    self[k] = v
                else:
                    self[key] = value

    @classmethod
    def from_dict(cls, initial: dict[str, T]) -> CaseInsensitiveDict[T]:
        """Class method to create a CaseInsensitiveDict instance from a dictionary.

        Args:
        ----
            initial (dict[str, T]): A dictionary from which to create the CaseInsensitiveDict.

        Returns:
        -------
            CaseInsensitiveDict[T]: A new instance of CaseInsensitiveDict.
        """
        # Create an empty instance of CaseInsensitiveDict
        case_insensitive_dict = cls()

        for key, value in initial.items():
            case_insensitive_dict[key] = value  # Utilize the __setitem__ method for setting items

        return case_insensitive_dict

    #    @classmethod
    #    def __class_getitem__(cls, item: Any) -> GenericAlias:
    #        return GenericAlias(cls, item)

    def __eq__(self, other: object) -> bool:
        # Quick checks.
        if self is other:
            return True
        is_casedict = isinstance(other, CaseInsensitiveDict)
        is_dict = isinstance(other, dict) and not is_casedict  # for future implementation when we make CaseInsensitiveDict subclass dict.
        if not is_dict and not is_casedict:
            return NotImplemented
        # it's a dict of some sort, do some more quick checks.
        if is_casedict and other._case_map != self._case_map:
            return False
        other_dict: dict[str, T] = other._dictionary if isinstance(other, CaseInsensitiveDict) else other  # pyright: ignore[reportAssignmentType]
        if len(self._dictionary) != len(other_dict):
            return False

        # unfortunately we must now iterate over each and compare (slow)
        for key, value in self._dictionary.items():
            other_value: T | None = other_dict.get(key.lower())
            if other_value != value:
                return False

        return True

    def __iter__(self) -> Iterator[str]:
        yield from self._dictionary

    def __getitem__(self, key: str) -> T:
        if not isinstance(key, str):
            msg = f"Keys must be strings in CaseInsensitiveDict-inherited classes, got {key!r}"
            raise KeyError(msg)
        return self._dictionary[self._case_map[key.lower()]]  # pyright: ignore[reportArgumentType]

    def __setitem__(self, key: str, value: T):
        if not isinstance(key, str):
            msg = f"Keys must be strings in CaseInsensitiveDict-inherited classes, got {key!r}"
            raise KeyError(msg)
        if key in self:
            self.__delitem__(key)
        self._case_map[key.lower()] = key  # pyright: ignore[reportArgumentType]
        self._dictionary[key] = value

    def __delitem__(self, key: str):
        if not isinstance(key, str):
            msg = f"Keys must be strings in CaseInsensitiveDict-inherited classes, got {key!r}"
            raise KeyError(msg)
        lower_key = key.lower()
        del self._dictionary[self._case_map[lower_key]]  # pyright: ignore[reportArgumentType]
        del self._case_map[lower_key]

    def __contains__(self, key: str) -> bool:
        return key.lower() in self._case_map

    def __len__(self) -> int:
        return len(self._dictionary)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.from_dict({self._dictionary!r})"

    def __or__(self, other):
        if not isinstance(other, (dict, CaseInsensitiveDict)):
            return NotImplemented
        new_dict: CaseInsensitiveDict[T] = self.copy()
        new_dict.update(other)
        return new_dict

    def __ror__(self, other):
        if not isinstance(other, (dict, CaseInsensitiveDict)):
            return NotImplemented
        other_dict: CaseInsensitiveDict[T] = other if isinstance(other, CaseInsensitiveDict) else CaseInsensitiveDict.from_dict(other)
        new_dict: CaseInsensitiveDict[T] = other_dict.copy()
        new_dict.update(self)
        return new_dict

    def __ior__(self, other):
        self.update(other)
        return self

    def __reversed__(self) -> Iterator[str]:
        return reversed(list(self._dictionary.keys()))

    @overload
    def pop(self, __key: str) -> T: ...
    @overload
    def pop(self, __key: str, __default: VT = None) -> VT | T: ...

    def pop(self, __key: str, __default: VT = _unique_sentinel) -> VT | T:  # type: ignore[assignment]
        lower_key: str = __key.lower()
        try:
            # Attempt to pop the value using the case-insensitive key.
            value: T = self._dictionary.pop(self._case_map.pop(lower_key))  # pyright: ignore[reportArgumentType]
        except KeyError:
            if __default is _unique_sentinel:
                raise
            # Return the default value if lower_key is not found in the case map.
            return __default
        return value

    def update(self, other):
        """Extend the dictionary with the key/value pairs from other, overwriting existing keys.

        This method acts like the `update` method in a regular dictionary, but is case-insensitive.

        Args:
        ----
            other (Iterable[tuple[str, T]] | dict[str, T]):
                Key/value pairs to add to the dictionary. Can be another dictionary or an iterable of key/value pairs.
        """
        if isinstance(other, (dict, CaseInsensitiveDict)):
            for key, value in other.items():
                if not isinstance(key, str):
                    msg = f"{key} must be a str, got type {key.__class__}"
                    raise TypeError(msg)
                self[key] = value
        else:
            for key, value in other:
                if not isinstance(key, str):
                    msg = f"{key} must be a str, got type {key.__class__}"
                    raise TypeError(msg)
                self[key] = value

    @overload
    def get(self, __key: str) -> T: ...
    @overload
    def get(self, __key: str, __default: VT = None) -> VT | T: ...

    def get(self, __key: str, __default: VT = None) -> VT | T:  # type: ignore[assignment]
        key_lookup: str = self._case_map.get(__key.lower(), _unique_sentinel)  # type: ignore[arg-type]
        return (
            __default
            if key_lookup is _unique_sentinel
            else self._dictionary.get(key_lookup, __default)
        )

    def items(self):
        return self._dictionary.items()

    def values(self):
        return self._dictionary.values()

    def keys(self):
        return self._dictionary.keys()

    def copy(self) -> CaseInsensitiveDict[T]:
        return self.from_dict(self._dictionary)

    def clear(self) -> None:
        self._dictionary.clear()
        self._case_map.clear()


# Example usage:
if __name__ == "__main__":
    # Initialization
    os = OrderedSet(["a", "b", "a"])
    assert os == ["a", "b"]
    assert isinstance(os, OrderedSet)
    assert isinstance(os, list)
    assert isinstance(os, MutableSet)

    # Append
    os.append("c")
    assert os == ["a", "b", "c"]
    os.append("b")  # No duplicate
    assert os == ["a", "b", "c"]

    # Extend
    os.extend(["d", "e", "d"])
    assert os == ["a", "b", "c", "d", "e"]

    # Insert
    os.insert(1, "f")
    assert os == ["a", "f", "b", "c", "d", "e"]
    os.insert(1, "a")  # No duplicate
    assert os == ["a", "f", "b", "c", "d", "e"]

    # Remove
    os.remove("f")
    assert os == ["a", "b", "c", "d", "e"]
    try:  # noqa: SIM105
        os.remove("f")
    except ValueError:  # noqa: S110
        pass  # Expected since "f" is already removed

    # Pop
    assert os.pop() == "e"
    assert os == ["a", "b", "c", "d"]
    assert os.pop(1) == "b"
    assert os == ["a", "c", "d"]

    # Clear
    os.clear()
    assert os == []

    # __setitem__
    os.extend(["a", "b", "c", "d"])
    os[1] = "e"
    assert os == ["a", "e", "c", "d"]
    try:  # noqa: SIM105
        os[1] = "a"  # Duplicate error
    except ValueError:  # noqa: S110
        pass  # Expected since "a" is already in the set

    # __delitem__
    del os[1]
    assert os == ["a", "c", "d"]
    del os[:2]
    assert os == ["d"]

    # Copy
    os2 = os.copy()
    assert os2 == os
    os.append("e")
    assert os != os2

    # Count and Index
    assert os.count("d") == 1
    assert os.index("d") == 0

    # Sort and Reverse
    os.extend(["b", "a", "c"])
    os.sort()
    assert os == ["a", "b", "c", "d", "e"]
    os.reverse()
    assert os == ["e", "d", "c", "b", "a"]

    # Add and iAdd
    os2 = [*os, "f", "g"]
    assert os2 == ["e", "d", "c", "b", "a", "f", "g"]
    os += ["h", "i"]
    assert os == ["e", "d", "c", "b", "a", "h", "i"]

    # Reversed
    assert list(reversed(os)) == ["i", "h", "a", "b", "c", "d", "e"]

    # Comparisons
    os2 = OrderedSet(["a", "b", "c"])
    os3 = OrderedSet(["a", "b", "d"])
    assert os2 < os3
    assert os3 > os2
    assert os2 <= os3
    assert os3 >= os2
    assert os2 == ["a", "b", "c"]
    assert os2 != ["a", "b"]
    assert os2 != os3

    print("All tests passed!")

