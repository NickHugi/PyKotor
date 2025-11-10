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
            return (self._content, "", "")

        idx: int = match.start()
        sep_length: int = len(__sep)
        return (
            self._content[:idx],
            self._content[idx : idx + sep_length],
            self._content[idx + sep_length :],
        )

    def rpartition(
        self,
        __sep,
    ):
        # Find the position of the separator in a case-insensitive manner
        pattern: re.Pattern[str] = re.compile(re.escape(self._coerce_str(__sep)), re.IGNORECASE)
        matches = list(pattern.finditer(self._content))

        if not matches:
            return ("", "", self._content)
        match: re.Match[str] = matches[-1]  # Get the last match for rpartition
        idx: int = match.start()
        return (
            self._content[:idx],
            self._content[idx : idx + len(__sep)],
            self._content[idx + len(__sep) :],
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
        start_idx = 0 if __start is None else int(__start)
        end_idx = len(self._content) if __end is None else int(__end)
        slice_text = self._casefold_content[start_idx:end_idx]
        target = self._coerce_str(__sub)
        result = slice_text.rfind(target)
        if result == -1:
            return -1
        if __start is None and __end is None:
            return result
        return result

    def split(
        self,
        sep=None,
        maxsplit: int = -1,
    ) -> list[str]:
        if sep is None:
            return self._content.split(None, maxsplit)

        sep_str = str(sep)
        if sep_str == "":
            msg = "empty separator"
            raise ValueError(msg)

        pattern: re.Pattern[str] = re.compile(re.escape(sep_str), re.IGNORECASE)
        maxsplit_arg = maxsplit if maxsplit is not None and maxsplit >= 0 else 0
        parts = pattern.split(self._content, maxsplit_arg)
        return parts

    def _split_by_indices(
        self,
        indices: list[int | tuple[int, int]],
        maxsplit: int,
        reverse: bool = False,
    ) -> list[Self]:
        if maxsplit == 0:
            return [self.__class__(self._content)]

        spans: list[tuple[int, int]] = []
        for entry in indices:
            if isinstance(entry, tuple):
                spans.append(entry)
            else:
                spans.append((entry, entry + 1))

        if reverse:
            spans = list(reversed(spans))

        parts: list[Self] = []
        splits_done = 0

        if not reverse:
            last_index = 0
            for start, end in spans:
                segment = self.__class__(self._content[last_index:start])
                parts.append(segment)
                splits_done += 1

                if maxsplit != -1 and splits_done >= maxsplit:
                    parts[-1] = self.__class__(self._content[last_index:])
                    return parts

                parts.append(self.__class__(self._content[start:end]))
                last_index = end

            parts.append(self.__class__(self._content[last_index:]))
            return parts

        # reverse=True handling
        content_len = len(self._content)
        last_index = content_len
        temp_parts: list[Self] = []

        for start, end in spans:
            # spans are already reversed order; adjust to actual coordinates
            adj_start, adj_end = content_len - end, content_len - start
            segment = self.__class__(self._content[adj_end:last_index])
            temp_parts.append(segment)
            splits_done += 1

            if maxsplit != -1 and splits_done >= maxsplit:
                temp_parts[-1] = self.__class__(self._content[:last_index])
                return list(reversed(temp_parts))

            temp_parts.append(self.__class__(self._content[adj_start:adj_end]))
            last_index = adj_start

        temp_parts.append(self.__class__(self._content[:last_index]))
        return list(reversed(temp_parts))

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
        prefix_str = str(__prefix)
        if self._content.startswith(prefix_str):
            return self.__class__(self._content[len(prefix_str) :])
        return self.__class__(self._content)

    def removesuffix(
        self,
        __suffix: WrappedStr | str,
    ) -> Self:
        suffix_str = str(__suffix)
        if self._content.endswith(suffix_str):
            return self.__class__(self._content[: -len(suffix_str)])
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
    ) -> list[str]:
        if __sep is None:
            return self._content.rsplit(None, __maxsplit)

        sep_str = str(__sep)
        if sep_str == "":
            msg = "empty separator"
            raise ValueError(msg)

        pattern: re.Pattern[str] = re.compile(re.escape(sep_str), re.IGNORECASE)
        matches = list(pattern.finditer(self._content))
        if not matches:
            return [self._content]

        if __maxsplit is not None and __maxsplit > 0:
            matches = matches[-__maxsplit:]

        parts: list[str] = []
        last_index = len(self._content)
        for match in reversed(matches):
            start, end = match.span()
            parts.append(self._content[end:last_index])
            last_index = start
        parts.append(self._content[:last_index])
        return list(reversed(parts))

    def rindex(
        self,
        __sub: WrappedStr | str,
        __start: SupportsIndex | None = None,
        __end: SupportsIndex | None = None,
    ) -> int:
        value = self.rfind(__sub, __start, __end)
        if value == -1:
            msg = "substring not found"
            raise ValueError(msg)
        return value

    def startswith(
        self,
        __prefix: WrappedStr | str | tuple[WrappedStr | str, ...],
        __start: SupportsIndex | None = None,
        __end: SupportsIndex | None = None,
    ) -> bool:
        parsed_prefix: tuple[str, ...] | str = tuple(self._coerce_str(s) for s in __prefix) if isinstance(__prefix, tuple) else self._coerce_str(__prefix)
        return self._casefold_content.startswith(parsed_prefix, __start, __end)
