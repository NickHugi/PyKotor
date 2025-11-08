from __future__ import annotations

import pathlib
import sys

from contextlib import suppress
from itertools import zip_longest
from typing import Any, Callable, ClassVar, Sequence

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve().parent
PYKOTOR_LIB = THIS_SCRIPT_PATH.parents[5].joinpath("Libraries", "PyKotor", "src")
UTILITY_LIB = THIS_SCRIPT_PATH.parents[5].joinpath("Libraries", "Utility", "src")
for lib_path in (PYKOTOR_LIB, UTILITY_LIB):
    lib_str = str(lib_path)
    if lib_path.exists() and lib_str not in sys.path:
        sys.path.append(lib_str)

from utility.string_util import compare_and_format, format_text  # type: ignore[attr-defined]  # noqa: E402


class ComparableMixin:
    """Mixin that provides a dynamic, field-driven compare() implementation.

    Subclasses should define class variables to describe which attributes are
    compared as scalars and which are compared as sequences of items:

    - COMPARABLE_FIELDS: tuple[str, ...]
        Attribute names whose values are compared directly (or recursively if
        they are also ComparableMixin instances).

    - COMPARABLE_SEQUENCE_FIELDS: tuple[str, ...]
        Attribute names whose values are sequences. The compare will check
        length, then compare elements pairwise (recursively if elements are
        ComparableMixin instances).
    """

    COMPARABLE_FIELDS: ClassVar[tuple[str, ...]] = ()
    COMPARABLE_SEQUENCE_FIELDS: ClassVar[tuple[str, ...]] = ()
    COMPARABLE_SET_FIELDS: ClassVar[tuple[str, ...]] = ()

    # Float tolerance for approximate comparisons
    _FLOAT_REL_TOL: ClassVar[float] = 1e-4
    _FLOAT_ABS_TOL: ClassVar[float] = 1e-4

    def compare(
        self,
        other: object,
        log_func: Callable[[str], Any] = print,
    ) -> bool:  # noqa: D401
        """Dynamically compare this object to another of the same type.

        Returns True when considered equal; logs differences via log_func.
        """
        if not isinstance(other, self.__class__):
            log_func(f"Type mismatch: '{self.__class__.__name__}' vs '{other.__class__.__name__ if isinstance(other, object) else type(other)}'")
            return False

        is_same: bool = True

        # Compare scalar fields
        for field_name in getattr(self, "COMPARABLE_FIELDS", ()):
            try:
                old_value = getattr(self, field_name)
                new_value = getattr(other, field_name)
            except AttributeError:
                log_func(f"Missing attribute '{field_name}' on one of the objects")
                is_same = False
                continue

            if not self._compare_values(field_name, old_value, new_value, log_func):
                is_same = False

        # Compare set-like fields (unordered)
        for set_name in getattr(self, "COMPARABLE_SET_FIELDS", ()):  # sourcery skip: for-append-to-extend
            try:
                old_set_raw = getattr(self, set_name)
                new_set_raw = getattr(other, set_name)
            except AttributeError as e:
                log_func(f"Missing set attribute '{set_name}' on one of the objects: {e.__class__.__name__}: {e}")
                is_same = False
                continue

            try:
                old_set = set(old_set_raw)
                new_set = set(new_set_raw)
            except Exception as e:  # noqa: BLE001
                log_func(f"Error converting set '{set_name}' to set: {e.__class__.__name__}: {e}")
                # Fallback to direct value compare if not set-like
                if not self._compare_values(set_name, old_set_raw, new_set_raw, log_func):
                    is_same = False
                continue

            if old_set == new_set:
                continue

            missing_items = old_set - new_set
            extra_items = new_set - old_set
            if missing_items:
                log_func(f"Set '{set_name}' missing items in new: {len(missing_items)}")
                for item in missing_items:
                    log_func(format_text(item))
            if extra_items:
                log_func(f"Set '{set_name}' has extra items in new: {len(extra_items)}")
                for item in extra_items:
                    log_func(format_text(item))
            is_same = False

        # Compare sequence fields (ordered)
        for seq_name in getattr(self, "COMPARABLE_SEQUENCE_FIELDS", ()):
            try:
                old_seq: Sequence[Any] = getattr(self, seq_name)
                new_seq: Sequence[Any] = getattr(other, seq_name)
            except AttributeError:
                log_func(f"Missing sequence attribute '{seq_name}' on one of the objects")
                is_same = False
                continue

            if len(old_seq) != len(new_seq):
                log_func(f"List '{seq_name}' length mismatch. Old: {len(old_seq)}, New: {len(new_seq)}")
                is_same = False

            for index, (old_item, new_item) in enumerate(
                zip_longest(old_seq, new_seq, fillvalue=None)
            ):
                if old_item is None and new_item is None:
                    continue
                if old_item is None:
                    log_func(f"New-only item at {seq_name}[{index}]: {format_text(new_item)}")
                    is_same = False
                    continue
                if new_item is None:
                    log_func(f"Old-only item at {seq_name}[{index}]: {format_text(old_item)}")
                    is_same = False
                    continue

                # Nested comparison or direct equality
                nested_same = self._compare_items_in_sequence(
                    seq_name,
                    index,
                    old_item,
                    new_item,
                    log_func,
                )
                if not nested_same:
                    is_same = False

        return is_same

    # Internal helpers
    def _compare_items_in_sequence(
        self,
        seq_name: str,
        index: int,
        old_item: Any,
        new_item: Any,
        log_func: Callable[[str], Any],
    ) -> bool:
        # If items are themselves Comparable, use their compare() with a prefixed logger
        if isinstance(old_item, ComparableMixin) and isinstance(new_item, ComparableMixin):
            prefixed = self._prefixed_logger(log_func, f"{seq_name}[{index}] ")
            return old_item.compare(new_item, prefixed)

        # Otherwise, basic equality (with float tolerance) and diff output
        if self._values_equal(old_item, new_item):
            return True

        log_func(f"Mismatch at {seq_name}[{index}]")
        old_fmt, new_fmt = compare_and_format(old_item, new_item)
        log_func(format_text(old_fmt))
        log_func(format_text(new_fmt))
        return False

    def _compare_values(
        self,
        name: str,
        old_value: Any,
        new_value: Any,
        log_func: Callable[[str], Any],
    ) -> bool:
        # Recurse for nested Comparable values
        if isinstance(old_value, ComparableMixin) and isinstance(new_value, ComparableMixin):
            prefixed = self._prefixed_logger(log_func, f"{name}. ")
            return old_value.compare(new_value, prefixed)

        # Equality (with float tolerance) and diff output
        if self._values_equal(old_value, new_value):
            return True

        log_func(f"Field '{name}' mismatch")
        old_fmt, new_fmt = compare_and_format(old_value, new_value)
        log_func(format_text(old_fmt))
        log_func(format_text(new_fmt))
        return False

    @classmethod
    def _values_equal(cls, a: Any, b: Any) -> bool:
        # Fast path
        if a is b:
            return True
        # Approximate float comparison
        with suppress(Exception):
            import math  # type: ignore[attr-defined]  # noqa: PLC0415

            if isinstance(a, float) and isinstance(b, float):
                return math.isclose(a, b, rel_tol=cls._FLOAT_REL_TOL, abs_tol=cls._FLOAT_ABS_TOL)

        return a == b

    @staticmethod
    def _prefixed_logger(log_func: Callable[[str], Any], prefix: str) -> Callable[[str], Any]:
        def _inner(msg: str) -> Any:
            return log_func(f"{prefix}{msg}")

        return _inner


