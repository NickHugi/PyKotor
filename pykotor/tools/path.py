from __future__ import annotations

import os
import pathlib
import platform
from typing import TYPE_CHECKING, Any, Callable, Generator, List, Tuple, Union

from pykotor.helpers.misc import is_instance_or_subinstance
from pykotor.helpers.path import Path as InternalPath
from pykotor.helpers.path import PurePath as InternalPurePath
from pykotor.helpers.registry import resolve_reg_key_to_path
from pykotor.tools.registry import winreg_key

if TYPE_CHECKING:
    from pykotor.common.misc import Game

PathElem = Union[str, os.PathLike]
PATH_TYPES = Union[PathElem, List[PathElem], Tuple[PathElem, ...]]


def simple_wrapper(fn_name, wrapped_class_type) -> Callable[..., Any]:
    def wrapped(self, *args, **kwargs) -> Any:
        orig_fn = wrapped_class_type._original_methods[fn_name]

        def parse_arg(arg):
            if is_instance_or_subinstance(arg, InternalPurePath) and CaseAwarePath.should_resolve_case(arg):
                return CaseAwarePath._get_case_sensitive_path(arg)

            return arg

        # Parse `self` if it meets the condition
        actual_self_or_cls: CaseAwarePath | type = parse_arg(self)

        # Handle positional arguments
        args = tuple(parse_arg(arg) for arg in args)

        # Handle keyword arguments
        kwargs = {k: parse_arg(v) for k, v in kwargs.items()}

        # TODO: when orig_fn doesn't exist, the AttributeException should be raised by
        # the prior stack instead of here, as that's what would normally happen.

        return orig_fn(actual_self_or_cls, *args, **kwargs)

    return wrapped


def create_case_insensitive_pathlib_class(cls) -> None:
    # Create a dictionary that'll hold the original methods for this class
    cls._original_methods = {}
    mro = cls.mro()  # Gets the method resolution order
    parent_classes = mro[1:-1]  # Exclude the current class itself

    # Store already wrapped methods to avoid wrapping multiple times
    wrapped_methods = set()

    # ignore these methods
    ignored_methods: set[str] = {
        "__instancecheck__",
        "__getattribute__",
        "__setattribute__",
        "__str__",
        "__repr__",
        "_fix_path_formatting",
        "__eq__",
        "__hash__",
        "__getattr__",
        "__setattr__",
        "__init__",
        "_init",
    }

    for parent in parent_classes:
        for attr_name, attr_value in parent.__dict__.items():
            # Check if it's a method and hasn't been wrapped before
            if callable(attr_value) and attr_name not in wrapped_methods and attr_name not in ignored_methods:
                cls._original_methods[attr_name] = attr_value
                setattr(cls, attr_name, simple_wrapper(attr_name, cls))
                wrapped_methods.add(attr_name)


class CaseAwarePath(InternalPath):
    """A class capable of resolving case-sensitivity in a path. Absolutely essential for working with KOTOR files."""

    def resolve(self, strict=False):
        new_path = super().resolve(strict)
        if self.should_resolve_case(new_path):
            new_path = self._get_case_sensitive_path(new_path)
        return new_path

    # Call __eq__ when using 'in' keyword
    def __contains__(self, other_path: os.PathLike | str):
        return super().__eq__(other_path)

    def __hash__(self):
        """Ensures any instance of this class will be treated the same in lists etc, if they're case-insensitive matches."""
        return hash((self.__class__.__name__, super().__str__().lower()))

    def __eq__(self, other: object):
        """All pathlib classes that derive from PurePath are equal to this object if their str paths are case-insensitive equivalents."""
        if not isinstance(other, (os.PathLike, str)):
            return NotImplemented
        other = other.as_posix() if isinstance(other, pathlib.PurePath) else str(other)
        return self._fix_path_formatting(other).lower() == super().__str__().lower()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({super().__str__().lower()})"

    def __str__(self) -> str:
        return (
            super().__str__()
            if pathlib.Path(self).exists()
            else super(self.__class__, self._get_case_sensitive_path(self)).__str__()
        )

    @staticmethod
    def _get_case_sensitive_path(path: os.PathLike | str) -> CaseAwarePath:
        pathlib_path: pathlib.Path = pathlib.Path(path)
        parts = list(pathlib_path.parts)

        for i in range(1, len(parts)):  # ignore the root (/, C:\\, etc)
            base_path: InternalPath = InternalPath(*parts[:i])
            next_path: InternalPath = InternalPath(*parts[: i + 1])

            # Find the first non-existent case-sensitive file/folder in hierarchy
            if not next_path.safe_isdir() and base_path.safe_isdir():
                base_path_items_generator = (
                    item for item in base_path.safe_iterdir() if (i == len(parts) - 1) or item.safe_isdir()
                )

                # if multiple are found, use the one that most closely matches our case
                # A closest match is defined in this context as the file/folder's name which has the most case-sensitive positional character matches
                # If two closest matches are identical (e.g. we're looking for TeST and we find TeSt and TesT), it's random.
                parts[i] = CaseAwarePath._find_closest_match(
                    parts[i],
                    base_path_items_generator,
                )

            # return a CaseAwarePath instance that resolves the case of existing items on disk, joined with the non-existing
            # parts in their original case.
            # if parts[1] is not found on disk, i.e. when i is 1 and base_path.exists() returns False, this will also return the original path.
            elif not next_path.safe_exists():
                return CaseAwarePath._create_instance(base_path.joinpath(*parts[i:]))

        # return a CaseAwarePath instance
        return CaseAwarePath._create_instance(*parts)

    @classmethod
    def _find_closest_match(cls, target, candidates: Generator[InternalPath, None, None]) -> str:
        max_matching_chars = -1
        closest_match = target
        for candidate in candidates:
            matching_chars = cls._get_matching_characters_count(
                candidate.name,
                target,
            )
            if matching_chars > max_matching_chars:
                max_matching_chars = matching_chars
                closest_match = candidate.name
                if max_matching_chars == len(target):
                    break
        return closest_match

    @staticmethod
    def _get_matching_characters_count(str1: str, str2: str) -> int:
        """Returns the number of case sensitive characters that match in each position of the two strings.
        if str1 and str2 are NOT case-insensitive matches, this method will return -1.
        """
        return sum(a == b for a, b in zip(str1, str2)) if str1.lower() == str2.lower() else -1

    @staticmethod
    def should_resolve_case(path: os.PathLike | str) -> bool:
        if os.name == "nt":
            return False
        path_obj = pathlib.Path(path)
        return path_obj.is_absolute() and not path_obj.exists()


# HACK: fix later
if os.name == "posix":
    create_case_insensitive_pathlib_class(CaseAwarePath)
elif os.name == "nt":
    CaseAwarePath = InternalPath  # type: ignore[assignment, misc]


def get_default_paths():
    from pykotor.common.misc import Game

    return {
        "Windows": {
            Game.K1: [
                r"C:\Program Files\Steam\steamapps\common\swkotor",
                r"C:\Program Files (x86)\Steam\steamapps\common\swkotor",
                r"C:\Program Files\LucasArts\SWKotOR",
                r"C:\Program Files (x86)\LucasArts\SWKotOR",
                r"C:\GOG Games\Star Wars - KotOR",
            ],
            Game.K2: [
                r"C:\Program Files\Steam\steamapps\common\Knights of the Old Republic II",
                r"C:\Program Files (x86)\Steam\steamapps\common\Knights of the Old Republic II",
                r"C:\Program Files\LucasArts\SWKotOR2",
                r"C:\Program Files (x86)\LucasArts\SWKotOR2",
                r"C:\GOG Games\Star Wars - KotOR2",
            ],
        },
        "Darwin": {
            Game.K1: [
                "~/Library/Application Support/Steam/steamapps/common/swkotor/Knights of the Old Republic.app/Contents/Assets",
            ],
            Game.K2: [
                "~/Library/Application Support/Steam/steamapps/common/Knights of the Old Republic II/Knights of the Old Republic II.app/Contents/Assets",
            ],
        },
        "Linux": {
            Game.K1: [
                "~/.local/share/Steam/common/SteamApps/swkotor",
                "~/.local/share/Steam/common/steamapps/swkotor",
                "~/.local/share/Steam/common/swkotor",
                # wsl paths
                "/mnt/C/Program Files/Steam/steamapps/common/swkotor",
                "/mnt/C/Program Files (x86)/Steam/steamapps/common/swkotor",
                "/mnt/C/Program Files/LucasArts/SWKotOR",
                "/mnt/C/Program Files (x86)/LucasArts/SWKotOR",
                "/mnt/C/GOG Games/Star Wars - KotOR",
            ],
            Game.K2: [
                "~/.local/share/Steam/common/SteamApps/Knights of the Old Republic II",
                "~/.local/share/Steam/common/steamapps/Knights of the Old Republic II",
                "~/.local/share/Steam/common/Knights of the Old Republic II",
                # wsl paths
                "/mnt/C/Program Files/Steam/steamapps/common/Knights of the Old Republic II",
                "/mnt/C/Program Files (x86)/Steam/steamapps/common/Knights of the Old Republic II",
                "/mnt/C/Program Files/LucasArts/SWKotOR2",
                "/mnt/C/Program Files (x86)/LucasArts/SWKotOR2",
                "/mnt/C/GOG Games/Star Wars - KotOR2",
            ],
        },
    }


def find_kotor_paths_from_default() -> dict[Game, list[CaseAwarePath]]:
    """Finds paths to Knights of the Old Republic game data directories.

    Args:
    ----
        None
    Returns:
        dict[Game, list[CaseAwarePath]]: A dictionary mapping Games to lists of existing path locations.

    - Gets default hardcoded path locations from a lookup table
    - Resolves paths and filters out non-existing ones
    - On Windows, also searches the registry for additional locations
    - Returns results as lists for each Game rather than sets
    """
    from pykotor.common.misc import Game

    os_str = platform.system()

    # Build hardcoded default kotor locations
    raw_locations: dict[str, dict[Game, list[str]]] = get_default_paths()
    locations: dict[Game, set[CaseAwarePath]] = {
        game: {case_path for case_path in (CaseAwarePath(path).resolve() for path in paths) if case_path.exists()}
        for game, paths in raw_locations.get(os_str, {}).items()
    }

    # Build kotor locations by registry (if on windows)
    if os_str == "Windows":
        for game, possible_game_paths in ((Game.K1, winreg_key(Game.K1)), (Game.K2, winreg_key(Game.K2))):
            for reg_key, reg_valname in possible_game_paths:
                path_str = resolve_reg_key_to_path(reg_key, reg_valname)
                path = CaseAwarePath(path_str).resolve() if path_str else None
                if path and path.name and path.exists():
                    locations[game].add(path)

    # don't return nested sets, return as lists.
    return {Game.K1: [*locations[Game.K1]], Game.K2: [*locations[Game.K2]]}
