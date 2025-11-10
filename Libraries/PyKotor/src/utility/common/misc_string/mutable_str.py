from __future__ import annotations

import sys

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing_extensions import Self


def is_string_like(obj: Any) -> bool:  # sourcery skip: use-fstring-for-concatenation
    try:
        _ = obj + ""
    except Exception:  # pylint: disable=W0718  # noqa: BLE001
        return False
    else:
        return True


class WrappedStr(str):
    __slots__: tuple[str, ...] = ("_content",)

    def __init__(
        self,
        content: Self | str = "",
    ):
        if content is None:
            msg = f"Cannot initialize {self.__class__.__name__}(None), expected a str-like argument"
            raise RuntimeError(msg)
        if isinstance(content, WrappedStr):
            content = content._content  # noqa: SLF001
        self._content: str = content

    def __repr__(self):
        return f"WrappedStr({self._content!r})"

    def __reduce__(self):
        return (self.__class__, (self._content,))

    if not TYPE_CHECKING:  # Prevents pylance in vs code from bringing us here in 'go to definition'
        def __getattribute__(self, name: str):
            try:
                return super().__getattribute__(name)
            except AttributeError:
                return getattr(self._content, name)

    # region Forwards Compatibility
    if not hasattr(str, "__reduce_ex__"):
        def __reduce_ex__(self, protocol: int):
            if protocol >= 2:  # Protocol version 2 or higher uses a more efficient pickling format  # noqa: PLR2004
                return (self.__class__, (str(self),), None, None, None)
            return self.__reduce__()
    # endregion

    # region Backwards Compatibility
    @classmethod
    def _assert_str_or_none_type(
        cls: type[Self],
        var: Any,
    ) -> str:
        if var is None:
            return None  # type: ignore[return-value]
        if not isinstance(var, (cls, str)):
            msg = f"Expected str-like, got '{var}' of type {var.__class__}"
            raise TypeError(msg)
        return str(var)

    if not hasattr(str, "removeprefix"):
        def removeprefix(
            self,
            __prefix: WrappedStr | str,
        ) -> Self:
            parsed_prefix: str = self._assert_str_or_none_type(__prefix)
            if self._content.startswith(parsed_prefix):
                return self.__class__(self._content[len(parsed_prefix) :])
            return self.__class__(self._content)

    if not hasattr(str, "removesuffix"):
        def removesuffix(
            self,
            __suffix: WrappedStr | str,
        ) -> Self:
            parsed_suffix: str = self._assert_str_or_none_type(__suffix)
            if self._content.endswith(parsed_suffix):
                return self.__class__(self._content[: -len(parsed_suffix)])
            return self.__class__(self._content)
    def __getstate__(self) -> str:
        return self._content
    # endregion
