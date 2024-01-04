from __future__ import annotations

import os
import pathlib
import platform
from typing import TYPE_CHECKING, Any, Callable, Generator

from pykotor.tools.registry import winreg_key
from utility.misc import is_instance_or_subinstance
from utility.path import Path as InternalPath
from utility.path import PathElem
from utility.path import PurePath as InternalPurePath
from utility.registry import resolve_reg_key_to_path

if TYPE_CHECKING:
    from pykotor.common.misc import Game

def simple_wrapper(fn_name, wrapped_class_type) -> Callable[..., Any]:
    """Wraps a function to handle case-sensitive pathlib.PurePath arguments.

    This is a hacky way of ensuring that all args to any pathlib methods have their path case-sensitively resolved.
    This also resolves self, *args, and **kwargs for ensured accuracy.

    Args:
    ----
        fn_name: The name of the function to wrap
        wrapped_class_type: The class type that the function belongs to

    Returns:
    -------
        Callable[..., Any]: A wrapped function with the same signature as the original

    Processing Logic:
    ----------------
        1. Gets the original function from the class's _original_methods attribute
        2. Parses arguments that are paths, resolving case if needed
        3. Calls the original function with the parsed arguments.
    """
    def wrapped(self, *args, **kwargs) -> Any:
        """Wraps a function to handle case-sensitive path resolution.

        Args:
        ----
            self: The object the method is called on
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
        -------
            Any: The return value of the wrapped function

        Processing Logic:
        ----------------
            - Parse self, args and kwargs to resolve case-sensitive paths where needed
            - Call the original function, passing the parsed arguments
            - Return the result
        """
        orig_fn = wrapped_class_type._original_methods[fn_name]  # noqa: SLF001

        def parse_arg(arg):
            if is_instance_or_subinstance(arg, InternalPurePath) and CaseAwarePath.should_resolve_case(arg):
                return CaseAwarePath.get_case_sensitive_path(arg)
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


def create_case_insensitive_pathlib_class(cls: type) -> None:  # TODO: move into CaseAwarePath.__getattr__
    # Create a dictionary that'll hold the original methods for this class
    """Wraps methods of a pathlib class to be case insensitive.

    Args:
    ----
        cls: The pathlib class to wrap

    Processing Logic:
    ----------------
        1. Create a dictionary to store original methods
        2. Get the method resolution order and exclude current class
        3. Store already wrapped methods to avoid wrapping multiple times
        4. Loop through parent classes and methods
        5. Check if method and not wrapped before
        6. Add method to wrapped dictionary and reassign with wrapper.
    """
    cls._original_methods = {}  # type: ignore[attr-defined]
    mro: list[type] = cls.mro()  # Gets the method resolution order
    parent_classes: list[type] = mro[1:-1]  # Exclude the current class itself and the object class
    cls_methods: set[str] = {method for method in cls.__dict__ if callable(getattr(cls, method))}  # define names of methods in the cls, excluding inherited

    # Store already wrapped methods to avoid wrapping multiple times
    wrapped_methods = set()

    # ignore these methods
    ignored_methods: set[str] = {
        "__instancecheck__",
        "__getattribute__",
        "__setattribute__",
        "_fix_path_formatting",
        "__getattr__",
        "__setattr__",
        "__init__",
        "_init",
        "pathify",
        *cls_methods,
    }

    for parent in parent_classes:
        for attr_name, attr_value in parent.__dict__.items():
            # Check if it's a method and hasn't been wrapped before
            if callable(attr_value) and attr_name not in wrapped_methods and attr_name not in ignored_methods:
                cls._original_methods[attr_name] = attr_value  # type: ignore[attr-defined]
                setattr(cls, attr_name, simple_wrapper(attr_name, cls))
                wrapped_methods.add(attr_name)

 # TODO: Move to pykotor.common
class CaseAwarePath(InternalPath):  # type: ignore[misc]
    """A class capable of resolving case-sensitivity in a path. Absolutely essential for working with KOTOR files on Unix filesystems."""

    def resolve(self, strict=False):
        new_path = super().resolve(strict)
        if self.should_resolve_case(new_path):
            new_path = self.get_case_sensitive_path(new_path)
            return super(CaseAwarePath, new_path).resolve(strict)
        return new_path

    def __hash__(self) -> int:
        return hash(self.as_windows())

    def __eq__(self, other):
        """All pathlib classes that derive from PurePath are equal to this object if their str paths are case-insensitive equivalents."""
        if not isinstance(other, (os.PathLike, str)):
            print(f"Cannot compare {self!r} with {other!r}")
            return NotImplemented
        if isinstance(other, CaseAwarePath):
            return self.as_posix().lower() == other.as_posix().lower()

        return self._fix_path_formatting(str(other), slash="/").lower() == self.as_posix().lower()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.as_windows()})"

    def __str__(self) -> str:
        path_obj = pathlib.Path(self)
        return (
            self._fix_path_formatting(str(path_obj))
            if not self.should_resolve_case(path_obj)
            else super(CaseAwarePath, self.get_case_sensitive_path(path_obj)).__str__()
        )

    def relative_to(self, *args, walk_up=False, **kwargs):
        if not args or "other" in kwargs:
            raise TypeError("relative_to() missing 1 required positional argument: 'other'")  # noqa: TRY003, EM101

        other, *_deprecated = args
        parsed_other = self.with_segments(other, *_deprecated)
        for step, path in enumerate([parsed_other, *list(parsed_other.parents)]):  # noqa: B007
            if self.is_relative_to(path):
                break
            if not walk_up:
                raise ValueError(f"{str(self)!r} is not in the subpath of {str(parsed_other)!r}")  # noqa: TRY003, EM102
            if path.name == "..":
                raise ValueError(f"'..' segment in {str(parsed_other)!r} cannot be walked")  # noqa: TRY003, EM102
        else:
            raise ValueError(f"{str(self)!r} and {str(parsed_other)!r} have different anchors")  # noqa: TRY003, EM102

        parts: list[str] = [".."] * step + list(self.parts[step:])
        return self.with_segments(*parts)

    def is_relative_to(self, *args, **kwargs):
        """Return True if the path is relative to another path or False."""
        if not args or "other" in kwargs:
            raise TypeError("relative_to() missing 1 required positional argument: 'other'")  # noqa: TRY003, EM101

        other, *_deprecated = args
        parsed_other = self.with_segments(other, *_deprecated)
        return parsed_other == self or parsed_other in self.parents

    @staticmethod
    def get_case_sensitive_path(path: PathElem) -> CaseAwarePath:
        """Get a case sensitive path.

        Args:
        ----
            path: The path to resolve case sensitivity for

        Returns:
        -------
            CaseAwarePath: The path with case sensitivity resolved

        Processing Logic:
        ----------------
            - Convert the path to a pathlib Path object
            - Iterate through each path part starting from index 1
            - Check if the current path part and the path up to that part exist
            - If not, find the closest matching file/folder name in the existing path
            - Return a CaseAwarePath instance with case sensitivity resolved.
        """
        pathlib_path: pathlib.Path = pathlib.Path(path)
        parts = list(pathlib_path.parts)

        for i in range(1, len(parts)):  # ignore the root (/, C:\\, etc)
            base_path: InternalPath = InternalPath(*parts[:i])
            next_path: InternalPath = InternalPath(*parts[: i + 1])

            # Find the first non-existent case-sensitive file/folder in hierarchy
            if not next_path.safe_isdir() and base_path.safe_isdir():

                # if multiple are found, use the one that most closely matches our case
                # A closest match is defined in this context as the file/folder's name which has the most case-sensitive positional character matches
                # If two closest matches are identical (e.g. we're looking for TeST and we find TeSt and TesT), it's random.
                last_part: bool = i == len(parts) - 1
                parts[i] = CaseAwarePath.find_closest_match(
                    parts[i],
                    (
                        item
                        for item in base_path.safe_iterdir()
                        if last_part or item.safe_isdir()
                    ),
                )

            elif not next_path.safe_exists():
                break

        # return a CaseAwarePath instance
        return CaseAwarePath._create_instance(*parts)

    @classmethod
    def find_closest_match(cls, target: str, candidates: Generator[InternalPath, None, None]) -> str:
        max_matching_chars: int = -1
        closest_match: str = target
        for candidate in candidates:
            matching_chars: int = cls.get_matching_characters_count(candidate.name, target)
            if matching_chars > max_matching_chars:
                closest_match = candidate.name
                if matching_chars == len(target):  # break if exact match
                    break
                max_matching_chars = matching_chars
        return closest_match

    @staticmethod
    def get_matching_characters_count(str1: str, str2: str) -> int:
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

if os.name != "nt":  # wrapping is unnecessary on Windows
    create_case_insensitive_pathlib_class(CaseAwarePath)

def get_default_paths() -> dict[str, dict[Game, list[str]]]:
    from pykotor.common.misc import Game

    return {
        "Windows": {
            Game.K1: [
                r"C:\Program Files\Steam\steamapps\common\swkotor",
                r"C:\Program Files (x86)\Steam\steamapps\common\swkotor",
                r"C:\Program Files\LucasArts\SWKotOR",
                r"C:\Program Files (x86)\LucasArts\SWKotOR",
                r"C:\GOG Games\Star Wars - KotOR",
                r"C:\Amazon Games\Library\Star Wars - Knights of the Old",
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
                "~/Library/Applications/Steam/steamapps/common/swkotor/Knights of the Old Republic.app/Contents/Assets/",
                # TODO: app store version of k1
            ],
            Game.K2: [
                "~/Library/Application Support/Steam/steamapps/common/Knights of the Old Republic II/Knights of the Old Republic II.app/Contents/Assets",
                "~/Library/Applications/Steam/steamapps/common/Knights of the Old Republic II/Star Wars™: Knights of the Old Republic II.app/Contents/GameData",
                "~/Applications/Knights of the Old Republic 2.app/Contents/Resources/transgaming/c_drive/Program Files/SWKotOR2/",
                "/Applications/Knights of the Old Republic 2.app/Contents/Resources/transgaming/c_drive/Program Files/SWKotOR2/",
            ],
        },
        "Linux": {
            Game.K1: [
                "~/.local/share/Steam/common/SteamApps/swkotor",
                "~/.local/share/Steam/common/steamapps/swkotor",
                "~/.local/share/Steam/common/swkotor",
                "~/.steam/root/steamapps/common/swkotor",  # executable name is `KOTOR1` no extension
                # wsl paths
                "/mnt/C/Program Files/Steam/steamapps/common/swkotor",
                "/mnt/C/Program Files (x86)/Steam/steamapps/common/swkotor",
                "/mnt/C/Program Files/LucasArts/SWKotOR",
                "/mnt/C/Program Files (x86)/LucasArts/SWKotOR",
                "/mnt/C/GOG Games/Star Wars - KotOR",
                "/mnt/C/Amazon Games/Library/Star Wars - Knights of the Old",
            ],
            Game.K2: [
                "~/.local/share/Steam/common/SteamApps/Knights of the Old Republic II",
                "~/.local/share/Steam/common/steamapps/Knights of the Old Republic II",
                "~/.local/share/aspyr-media/kotor2",
                "~/.local/share/Steam/common/Knights of the Old Republic II",
                "~/.steam/root/steamapps/common/Knights of the Old Republic II",  # executable name is `KOTOR2` no extension
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

    Returns
    -------
        dict[Game, list[CaseAwarePath]]: A dictionary mapping Games to lists of existing path locations.

    Processing Logic:
    ----------------
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
        game: {
            case_path
            for case_path in (CaseAwarePath(path).resolve() for path in paths)
            if case_path.exists()
        }
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
