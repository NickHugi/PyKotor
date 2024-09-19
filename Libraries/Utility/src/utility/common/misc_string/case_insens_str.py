from __future__ import annotations

import re

from typing import TYPE_CHECKING, Any

from utility.common.misc_string.mutable_str import WrappedStr

if TYPE_CHECKING:
    from typing_extensions import Self, SupportsIndex


class CaseInsensImmutableStr(WrappedStr):
    __slots__: tuple[str, ...] = ("_casefold_content",)

    @classmethod
    def _coerce_str(
        cls,
        item: Any,
    ) -> str:  # sourcery skip: assign-if-exp, reintroduce-else
        if isinstance(item, WrappedStr):
            return str(item._content).casefold()  # noqa: SLF001
        if isinstance(item, str):
            return str(item).casefold()
        return item

    def __init__(
        self,
        content: str | WrappedStr,
    ):
        super().__init__(content)
        self._casefold_content: str = str(content).casefold()

    def __contains__(
        self,
        __key,
    ):
        return self._casefold_content.__contains__(self._coerce_str(__key))

    def __eq__(
        self,
        __value,
    ):
        if self is __value:
            return True
        return self._casefold_content.__eq__(self._coerce_str(__value))

    def __ne__(
        self,
        __value,
    ):
        return self._casefold_content.__ne__(self._coerce_str(__value))

    def __hash__(self):
        return hash(self._casefold_content)

    def find(
        self,
        sub,
        start=0,
        end=None,
    ):
        return self._casefold_content.find(self._coerce_str(sub), start, end)

    def partition(
        self,
        __sep,
    ):
        # Find the position of the separator in a case-insensitive manner
        pattern: re.Pattern[str] = re.compile(re.escape(self._coerce_str(__sep)), re.IGNORECASE)
        match: re.Match[str] | None = pattern.search(self._content)

        if match is None:
            return (self.__class__(self._content), self.__class__(""), self.__class__(""))

        idx: int = match.start()
        sep_length: int = len(__sep)
        return (
            self.__class__(self._content[:idx]),
            self.__class__(self._content[idx:idx + sep_length]),
            self.__class__(self._content[idx + sep_length:]),
        )

    def rpartition(
        self,
        __sep,
    ):
        # Find the position of the separator in a case-insensitive manner
        pattern: re.Pattern[str] = re.compile(re.escape(self._coerce_str(__sep)), re.IGNORECASE)
        matches = list(pattern.finditer(self._content))

        if not matches:
            return (self.__class__(""), self.__class__(""), self.__class__(self._content))
        match: re.Match[str] = matches[-1]  # Get the last match for rpartition
        idx: int = match.start()
        return (
            self.__class__(self._content[:idx]),
            self.__class__(self._content[idx : idx + len(__sep)]),
            self.__class__(self._content[idx + len(__sep) :]),
        )

    def endswith(
        self,
        __suffix: WrappedStr | str | tuple[WrappedStr | str, ...],
        __start: SupportsIndex | None = None,
        __end: SupportsIndex | None = None,
    ) -> bool:
        """S.endswith(suffix[, start[, end]]) -> bool

        Return True if S ends with the specified suffix, False otherwise. With optional start, test S beginning at that position. With optional end, stop comparing S at that position. suffix can also be a tuple of strings to try.
        """  # noqa: D415, D400, D402
        parsed_suffix: tuple[str, ...] | str = tuple(self._coerce_str(s) for s in __suffix) if isinstance(__suffix, tuple) else self._coerce_str(__suffix)
        return self._casefold_content.endswith(parsed_suffix, __start, __end)

    def rfind(
        self,
        __sub,
        __start=None,
        __end=None,
    ):
        return self._casefold_content.rfind(self._coerce_str(__sub), __start, __end)

    def split(
        self,
        sep=None,
        maxsplit=-1,
    ):
        if sep is None:
            # Default split behavior on whitespace
            return super().split(None, maxsplit)

        # Case-insensitive split using regular expression
        pattern: re.Pattern[str] = re.compile(re.escape(self._coerce_str(sep)), re.IGNORECASE)
        split_parts: list[int] = [m.start() for m in pattern.finditer(self._content)]
        return self._split_by_indices(split_parts, int(maxsplit))

    def _split_by_indices(self, indices: list[int], maxsplit: int, reverse: bool = False) -> list[Self]:
        # Split the string using indices from the regular expression
        if maxsplit > 0:
            indices = indices[-maxsplit:] if reverse else indices[:maxsplit]

        last_index: int = 0
        results: list[Self] = []
        for index in reversed(indices) if reverse else indices:
            results.append(self.__class__(self._content[last_index:index]))
            last_index = index + 1

        results.append(self.__class__(self._content[last_index:]))
        return list(reversed(results)) if reverse else results

    def count(
        self,
        x: WrappedStr | str,
        __start: SupportsIndex | None = None,
        __end: SupportsIndex | None = None,
    ) -> int:
        return self._casefold_content.count(self._coerce_str(x), __start, __end)

    def index(
        self,
        __sub: WrappedStr | str,
        __start: SupportsIndex | None = None,
        __end: SupportsIndex | None = None,
    ) -> int:
        return self._casefold_content.index(self._coerce_str(__sub), __start, __end)

    def __lt__(
        self,
        __value: str | WrappedStr,
    ):
        return self._casefold_content < self._coerce_str(__value)

    def __le__(
        self,
        __value: str | WrappedStr,
    ):
        return self._casefold_content <= self._coerce_str(__value)

    def removeprefix(
        self,
        __prefix: WrappedStr | str,
    ) -> Self:
        parsed_prefix: str = self._coerce_str(__prefix)
        if self._casefold_content.startswith(parsed_prefix):
            return self.__class__(self._content[len(__prefix) :])
        return self.__class__(self._content)

    def removesuffix(
        self,
        __suffix: WrappedStr | str,
    ) -> Self:
        parsed_suffix: str = self._coerce_str(__suffix)
        if self._casefold_content.endswith(parsed_suffix):
            return self.__class__(self._content[: -len(__suffix)])
        return self.__class__(self._content)

    def replace(
        self,
        __old: WrappedStr | str,
        __new: WrappedStr | str,
        __count: int = -1,
    ) -> Self:
        """Return a copy with all occurrences of substring old replaced by new.

        count
            Maximum number of occurrences to replace. -1 (the default value) means replace all occurrences.

        If the optional argument count is given, only the first count occurrences are replaced.
        """
        if __old == "":
            # Handle empty string replacement
            return self.__class__(str.replace(self._content, __old, __new, __count))

        pattern = re.escape(str(__old))
        repl = str(__new)

        def case_preserving_repl(match: re.Match[str]) -> str:
            matched = match.group(0)
            if matched.isupper():
                return repl.upper()
            if matched.islower():
                return repl.lower()
            if matched[0].isupper():
                return repl.capitalize()
            return repl

        # Use re.finditer to find all matches
        matches = list(re.finditer(pattern, self._content, flags=re.IGNORECASE))

        # Limit the number of replacements if __count is specified
        if __count >= 0:
            matches = matches[:__count]

        # Perform replacements from right to left to avoid index issues
        new_content = self._content
        for match in reversed(matches):
            start, end = match.span()
            replacement = case_preserving_repl(match)
            new_content = new_content[:start] + replacement + new_content[end:]

        return self.__class__(new_content)

    def rsplit(
        self,
        __sep=None,
        __maxsplit=-1,
    ):
        if __sep is None:
            # Default split behavior on whitespace
            return [self.__class__(part) for part in self._content.rsplit(None, __maxsplit)]

        # Case-insensitive split using regular expression
        pattern: re.Pattern[str] = re.compile(re.escape(self._coerce_str(__sep)), re.IGNORECASE)
        split_parts: list[str] = pattern.split(self._content)

        if __maxsplit > 0:
            # Perform the split from the right
            split_parts = split_parts[-__maxsplit - 1 :]

        return [self.__class__(part) for part in split_parts]

    def rindex(
        self,
        __sub: WrappedStr | str,
        __start: SupportsIndex | None = None,
        __end: SupportsIndex | None = None,
    ) -> int:
        return self._casefold_content.rindex(self._coerce_str(__sub), __start, __end)

    def startswith(
        self,
        __prefix: WrappedStr | str | tuple[WrappedStr | str, ...],
        __start: SupportsIndex | None = None,
        __end: SupportsIndex | None = None,
    ) -> bool:
        parsed_prefix: tuple[str, ...] | str = tuple(self._coerce_str(s) for s in __prefix) if isinstance(__prefix, tuple) else self._coerce_str(__prefix)
        return self._casefold_content.startswith(parsed_prefix, __start, __end)
