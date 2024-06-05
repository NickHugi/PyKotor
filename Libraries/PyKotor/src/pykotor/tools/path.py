from __future__ import annotations

import os
import pathlib
import platform
import tempfile

from functools import lru_cache
from typing import TYPE_CHECKING, Any

from pykotor.tools.registry import find_software_key, winreg_key
from utility.string_util import ireplace
from utility.system.path import (
    Path as InternalPath,
    PosixPath as InternalPosixPath,
    PurePath as InternalPurePath,
    WindowsPath as InternalWindowsPath,
)
from utility.system.registry import resolve_reg_key_to_path

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from pykotor.common.misc import Game
    from utility.system.path import PathElem


def is_filesystem_case_sensitive(path: os.PathLike | str) -> bool | None:
    """Check if the filesystem at the given path is case-sensitive.
    This function creates a temporary file to test the filesystem behavior.
    """
    try:
        with tempfile.TemporaryDirectory(dir=path) as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            test_file = temp_path / "case_test_file"
            test_file.touch()

            # Attempt to access the same file with a different case to check case sensitivity
            test_file_upper = temp_path / "CASE_TEST_FILE"
            return not test_file_upper.exists()
    except Exception:
        return None


def simple_wrapper(fn_name: str, wrapped_class_type: type) -> Callable[..., Any]:
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
        # Do not use. CaseAwarePath's performance depends on only resolving case when it absolutely has to.
        # if fn_name == "__new__":
        #    path_obj = pathlib.Path(*args, **kwargs)
        #    if "called_from_getcase" not in kwargs and not path_obj.exists():
        #        return CaseAwarePath.get_case_sensitive_path(path_obj)

        def parse_arg(arg: Any) -> CaseAwarePath | Any:
            if not hasattr(arg, "__bases__") and hasattr(arg, "__fspath__") and arg.__class__ is not CaseAwarePath:
                pathlib_path_obj = pathlib.Path(arg)
                new_cls = arg.__class__
                if pathlib_path_obj.absolute() and not pathlib_path_obj.exists():
                    instance = CaseAwarePath.get_case_sensitive_path(arg)
                    if arg.__class__ in CaseAwarePath.__bases__ and arg.__class__ is not object:
                        return new_cls(instance)
                    return instance
            return arg

        # Parse `self` if it meets the condition
        actual_self_or_cls: CaseAwarePath | type = parse_arg(self)

        # Handle positional arguments
        new_args: tuple[CaseAwarePath | Any, ...] = tuple(parse_arg(arg) for arg in args)

        # Handle keyword arguments
        new_kwargs: dict[str, CaseAwarePath | Any] = {k: parse_arg(v) for k, v in kwargs.items()}

        # TODO: when orig_fn doesn't exist, the AttributeException should be raised by
        # the prior stack instead of here, as that's what would normally happen.

        return orig_fn(actual_self_or_cls, *new_args, **new_kwargs)

    return wrapped


def create_case_insensitive_pathlib_class(cls: type):  # TODO(th3w1zard1): move into CaseAwarePath.__getattr__
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
        "__fspath__",
        "__truediv__",
        "_fspath_str",
        "_init",
        "__new__",
        "pathify",
        *cls_methods,
    }

    for parent in parent_classes:
        for attr_name, attr_value in parent.__dict__.items():
            # Check if it's a method and hasn't been wrapped before
            if callable(attr_value) and attr_name not in wrapped_methods and attr_name not in ignored_methods:
                cls._original_methods[attr_name] = attr_value  # type: ignore[attr-defined]  # pylint: disable=protected-access
                setattr(cls, attr_name, simple_wrapper(attr_name, cls))
                wrapped_methods.add(attr_name)


# TODO: Move to pykotor.common
class CaseAwarePath(InternalWindowsPath if os.name == "nt" else InternalPosixPath):  # type: ignore[misc]
    """A class capable of resolving case-sensitivity in a path. Absolutely essential for working with KOTOR files on Unix filesystems."""

    __slots__ = ("_tail_cached",)

    @staticmethod
    def extract_absolute_prefix(relative_path: InternalPath, absolute_path: InternalPath) -> tuple[str, ...]:
        # Ensure the absolute path is absolute and the relative path is resolved relative to it
        absolute_path = absolute_path.absolute()
        relative_path_resolved = (absolute_path.parent / relative_path).absolute()

        # Convert to lists of parts for comparison
        abs_parts = absolute_path.parts
        rel_parts = relative_path_resolved.parts

        # Identify the index where the relative path starts in the absolute path
        start_index_of_rel_in_abs = len(abs_parts) - len(rel_parts)

        # Extract the differing prefix part as a new Path object
        return abs_parts[:start_index_of_rel_in_abs]

    def relative_to(
        self,
        *args: PathElem,
        walk_up: bool = False,
        **kwargs,
    ) -> InternalPath:
        if not args or "other" in kwargs:
            raise TypeError("relative_to() missing 1 required positional argument: 'other'")  # noqa: TRY003, EM101

        other, *_deprecated = args
        resolved_self = self
        if isinstance(resolved_self, InternalPath):
            if not isinstance(other, InternalPath):
                other = self.__class__(other)
            parsed_other = self.with_segments(other, *_deprecated).absolute()
            resolved_self = resolved_self.absolute()
        else:
            parsed_other = other if isinstance(other, InternalPurePath) else InternalPurePath(other)
            parsed_other = parsed_other.with_segments(other, *_deprecated)

        self_str, other_str = map(str, (resolved_self, parsed_other))
        replacement = ireplace(self_str, other_str, "").lstrip("\\").lstrip("/")
        if replacement == self_str:
            msg = f"self '{self_str}' is not relative to other '{other_str}'"
            raise ValueError(msg)

        if isinstance(self, CaseAwarePath) and not pathlib.Path(replacement).exists():
            prefixes = self.extract_absolute_prefix(InternalPath(replacement), InternalPath(parsed_other))
            return self.get_case_sensitive_path(replacement, prefixes)
        return self.__class__(replacement)

    @classmethod
    def get_case_sensitive_path(
        cls,
        path: PathElem,
        prefixes: list[str] | tuple[str, ...] | None = None,
    ):
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
        if os.name == "nt":
            return cls.pathify(path)

        prefixes = prefixes or []
        pathlib_path = pathlib.Path(path)
        pathlib_abspath = pathlib.Path(*prefixes, path).absolute() if prefixes else pathlib_path.absolute()
        num_differing_parts = len(pathlib_abspath.parts) - len(pathlib_path.parts)  # keeps the path relative if it already was.
        parts = list(pathlib_abspath.parts)

        for i in range(1, len(parts)):  # ignore the root (/, C:\\, etc)
            base_path: InternalPath = InternalPath(*parts[:i])
            next_path: InternalPath = InternalPath(*parts[: i + 1])

            if not next_path.safe_isdir() and base_path.safe_isdir():
                # Find the first non-existent case-sensitive file/folder in hierarchy
                # if multiple are found, use the one that most closely matches our case
                # A closest match is defined, in this context, as the file/folder's name that contains the most case-sensitive positional character matches
                # If two closest matches are identical (e.g. we're looking for TeST and we find TeSt and TesT), it's probably random.
                last_part: bool = i == len(parts) - 1
                parts[i] = cls.find_closest_match(
                    parts[i],
                    (item for item in base_path.safe_iterdir() if last_part or item.safe_isdir()),
                )

            elif not next_path.safe_exists():
                break

        # return a CaseAwarePath instance
        return cls._create_instance(*parts[num_differing_parts:], called_from_getcase=True)

    @classmethod
    def find_closest_match(
        cls,
        target: str,
        candidates: Generator[InternalPath, None, None],
    ) -> str:
        """Finds the closest match from candidates to the target string.

        Args:
        ----
            target: str - The target string to find closest match for
            candidates: Generator[pathlib.Path, None, None] - Generator of candidate paths

        Returns:
        -------
            str - The closest matching candidate's file/folder name from the candidates

        Processing Logic:
        ----------------
            - Initialize max_matching_chars to -1
            - Iterate through each candidate
            - Get the matching character count between candidate and target using get_matching_characters_count method
            - Update closest_match and max_matching_chars if new candidate has more matches
            - Return closest_match after full iteration.
            - If no exact match found, return target which will of course be nonexistent.
        """
        max_matching_chars: int = -1
        closest_match: str | None = None

        for candidate in candidates:
            matching_chars: int = cls.get_matching_characters_count(candidate.name, target)
            if matching_chars > max_matching_chars:
                closest_match = candidate.name
                if matching_chars == len(target):
                    break  # Exit the loop early if exact match (faster)
                max_matching_chars = matching_chars

        return closest_match or target

    @staticmethod
    @lru_cache(maxsize=10000)
    def get_matching_characters_count(str1: str, str2: str) -> int:
        """Returns the number of case sensitive characters that match in each position of the two strings.

        if str1 and str2 are NOT case-insensitive matches, this method will return -1.
        """
        return sum(a == b for a, b in zip(str1, str2)) if str1.lower() == str2.lower() else -1

    def __hash__(self):
        return hash(self.as_windows())

    def __eq__(self, other):
        """All pathlib classes that derive from PurePath are equal to this object if their str paths are case-insensitive equivalents."""
        if self is other:
            return True
        if not isinstance(other, (os.PathLike, str)):
            return NotImplemented
        if isinstance(other, CaseAwarePath):
            return self.as_posix().lower() == other.as_posix().lower()

        return self._fix_path_formatting(str(other), slash="/").lower() == self.as_posix().lower()

    def __repr__(self):
        str_path = self._flavour.sep.join(str(part) for part in self.parts)
        return f'{self.__class__.__name__}("{str_path}")'

    def __str__(self):
        path_obj = pathlib.Path(self)
        if os.name == "nt" or path_obj.exists():
            return super().__str__()

        case_resolved_path = self.get_case_sensitive_path(path_obj)
        return super(self.__class__, case_resolved_path).__str__()


if os.name != "nt":  # Wrapping is unnecessary on Windows
    create_case_insensitive_pathlib_class(CaseAwarePath)


def get_default_paths() -> dict[str, dict[Game, list[str]]]:
    from pykotor.common.misc import Game  # noqa: PLC0415  # pylint: disable=import-outside-toplevel

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
                "~/Library/Application Support/Steam/steamapps/common/swkotor/Knights of the Old Republic.app/Contents/Assets",  # Verified
                "~/Library/Applications/Steam/steamapps/common/swkotor/Knights of the Old Republic.app/Contents/Assets/",
                # TODO: app store version of k1
            ],
            Game.K2: [
                "~/Library/Application Support/Steam/steamapps/common/Knights of the Old Republic II/Knights of the Old Republic II.app/Contents/Assets",
                "~/Library/Applications/Steam/steamapps/common/Knights of the Old Republic II/Star Wars™: Knights of the Old Republic II.app/Contents/GameData",
                "~/Library/Application Support/Steam/steamapps/common/Knights of the Old Republic II/KOTOR2.app/Contents/GameData/",  # Verified
                # The following might be from a pirated version of the game, they were provided anonymously
                # It is also possible these are the missing app store paths.
                "~/Applications/Knights of the Old Republic 2.app/Contents/Resources/transgaming/c_drive/Program Files/SWKotOR2/",
                "/Applications/Knights of the Old Republic 2.app/Contents/Resources/transgaming/c_drive/Program Files/SWKotOR2/",
                # TODO: app store version of k2
            ],
        },
        "Linux": {
            Game.K1: [
                "~/.local/share/steam/common/steamapps/swkotor",
                "~/.local/share/steam/common/steamapps/swkotor",
                "~/.local/share/steam/common/swkotor",
                "~/.steam/debian-installation/steamapps/common/swkotor",  # verified
                "~/.steam/root/steamapps/common/swkotor",  # executable name is `KOTOR1` no extension
                # Flatpak
                "~/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/common/swkotor",
                # wsl paths
                "/mnt/C/Program Files/Steam/steamapps/common/swkotor",
                "/mnt/C/Program Files (x86)/Steam/steamapps/common/swkotor",
                "/mnt/C/Program Files/LucasArts/SWKotOR",
                "/mnt/C/Program Files (x86)/LucasArts/SWKotOR",
                "/mnt/C/GOG Games/Star Wars - KotOR",
                "/mnt/C/Amazon Games/Library/Star Wars - Knights of the Old",
            ],
            Game.K2: [
                "~/.local/share/Steam/common/steamapps/Knights of the Old Republic II",
                "~/.local/share/Steam/common/steamapps/kotor2",  # guess
                "~/.local/share/aspyr-media/kotor2",
                "~/.local/share/aspyr-media/Knights of the Old Republic II",  # guess
                "~/.local/share/Steam/common/Knights of the Old Republic II",  # ??? wrong?
                "~/.steam/debian-installation/steamapps/common/Knights of the Old Republic II",  # guess
                "~/.steam/debian-installation/steamapps/common/kotor2",  # guess
                "~/.steam/root/steamapps/common/Knights of the Old Republic II",  # executable name is `KOTOR2` no extension
                # Flatpak
                "~/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/common/Knights of the Old Republic II/steamassets",
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

    Returns:
    -------
        dict[Game, list[CaseAwarePath]]: A dictionary mapping Games to lists of existing path locations.

    Processing Logic:
    ----------------
        - Gets default hardcoded path locations from a lookup table
        - Resolves paths and filters out non-existing ones
        - On Windows, also searches the registry for additional locations
        - Returns results as lists for each Game rather than sets
    """
    from pykotor.common.misc import Game  # noqa: PLC0415  # pylint: disable=import-outside-toplevel

    os_str = platform.system()

    # Build hardcoded default kotor locations
    raw_locations: dict[str, dict[Game, list[str]]] = get_default_paths()
    locations: dict[Game, set[CaseAwarePath]] = {
        game: {case_path for case_path in (CaseAwarePath(path).expanduser().resolve() for path in paths) if case_path.safe_isdir()} for game, paths in raw_locations.get(os_str, {}).items()
    }

    # Build kotor locations by registry (if on windows)
    if os_str == "Windows":
        for game, possible_game_paths in ((Game.K1, winreg_key(Game.K1)), (Game.K2, winreg_key(Game.K2))):
            for reg_key, reg_valname in possible_game_paths:
                path_str = resolve_reg_key_to_path(reg_key, reg_valname)
                path = CaseAwarePath(path_str).resolve() if path_str else None
                if path and path.name and path.safe_isdir():
                    locations[game].add(path)
        amazon_k1_path_str: str | None = find_software_key("AmazonGames/Star Wars - Knights of the Old")
        if amazon_k1_path_str is not None and InternalPath(amazon_k1_path_str).safe_isdir():
            locations[Game.K1].add(CaseAwarePath(amazon_k1_path_str))

    # don't return nested sets, return as lists.
    return {Game.K1: [*locations[Game.K1]], Game.K2: [*locations[Game.K2]]}
