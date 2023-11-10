from __future__ import annotations

import contextlib
import os
import pathlib
import platform
import re
import sys
import uuid
from typing import TYPE_CHECKING, Any, Callable, Generator, List, Tuple, Union

if TYPE_CHECKING:
    from pykotor.common.misc import Game

PathElem = Union[str, os.PathLike]
PATH_TYPES = Union[PathElem, List[PathElem], Tuple[PathElem, ...]]


def has_attr_excluding_object(cls, attr_name) -> bool:
    # Exclude the built-in 'object' class
    mro_classes = [c for c in cls.mro() if c != object]

    return any(attr_name in base_class.__dict__ for base_class in mro_classes)


def is_class_or_subclass_but_not_instance(cls, target_cls) -> bool:
    if cls is target_cls:
        return True
    if not hasattr(cls, "__bases__"):
        return False
    return any(is_class_or_subclass_but_not_instance(base, target_cls) for base in cls.__bases__)


def is_instance_or_subinstance(instance, target_cls) -> bool:
    if hasattr(instance, "__bases__"):  # instance is a class
        return False  # if instance is a class type, always return False
    # instance is not a class
    return type(instance) is target_cls or is_class_or_subclass_but_not_instance(type(instance), target_cls)


def simple_wrapper(fn_name, wrapped_class_type) -> Callable[..., Any]:
    def wrapped(self, *args, **kwargs) -> Any:
        orig_fn = wrapped_class_type._original_methods[fn_name]

        def parse_arg(arg):
            if is_instance_or_subinstance(arg, PurePath) and CaseAwarePath.should_resolve_case(arg):
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


class BasePurePath:
    """BasePath is a class created to fix some annoyances with pathlib, such as its refusal to resolve mixed/repeating/trailing slashes."""

    def __new__(cls, *args: PATH_TYPES, **kwargs):
        return super().__new__(cls, *cls.parse_args(*args), **kwargs)

    def __init__(self, *args, _called_from_pathlib=True):
        next_init_method_class = next(
            (cls for cls in self.__class__.mro() if "__init__" in cls.__dict__ and cls is not BasePurePath),
            self.__class__,  # reminder: self.__class__ will never be BasePurePath
        )
        # Check if the class that defines the next __init__ is object
        if next_init_method_class is object:
            return

        # If not object, fetch the __init__ of that class
        init_method = next_init_method_class.__init__

        # Parse args if called from pathlib (Python 3.12+)
        if _called_from_pathlib:
            init_method(self, *self.parse_args(*args))
        else:
            init_method(self, *args)

    @classmethod
    def parse_args(cls, *args):
        args_list = list(args)
        for i, arg in enumerate(args_list):
            if isinstance(arg, cls):
                continue
            path_str = arg if isinstance(arg, str) else getattr(arg, "__fspath__", lambda: None)()
            if path_str is None:
                msg = f"Object '{arg}' (index {i} of *args) must be str or a path-like object, but instead was '{type(arg)}'"
                raise TypeError(msg)

            formatted_path_str = cls._fix_path_formatting(path_str, cls._flavour.sep)  # type: ignore[_flavour exists in children]
            arg_pathlib_instance = super().__new__(cls, formatted_path_str)  # type: ignore  # noqa: PGH003
            arg_pathlib_instance.__init__(formatted_path_str, _called_from_pathlib=False)
            args_list[i] = arg_pathlib_instance
        return args_list

    @classmethod
    def _create_instance(cls, *args, **kwargs):
        instance = cls.__new__(cls, *args, **kwargs)  # type: ignore  # noqa: PGH003
        instance.__init__(*args, **kwargs)
        return instance

    def __str__(self):
        """Call _fix_path_formatting before returning the pathlib class's __str__ result.
        In Python 3.12, pathlib's __str__ methods will return '' instead of '.', so we return '.' in this instance for backwards compatibility.
        """
        str_result = self.__class__._fix_path_formatting(super().__str__(), self._flavour.sep)  # type: ignore[_flavour exists in children]
        return "." if str_result == "" else str_result

    def __fspath__(self):
        """Ensures any use of __fspath__ will call our __str__ method."""
        return str(self)

    def __truediv__(self, key: PathElem):
        """Appends a path part with the divider operator '/'.
        This method is called when the left side is self.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object or str path):
        """
        return self._create_instance(self, key)

    def __rtruediv__(self, key: PathElem):
        """Appends a path part with the divider operator '/'.
        This method is called when the right side is self.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object or str path):
        """
        return self._create_instance(key, self)

    def __add__(self, key: PathElem) -> str:
        """Implicitly converts the path to a str when used with the addition operator '+'.
        This method is called when the left side is self.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object or str path):
        """
        return str(self) + str(key)

    def __radd__(self, key: PathElem) -> str:
        """Implicitly converts the path to a str when used with the addition operator '+'.
        This method is called when the right side is self.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object or str path):
        """
        return str(key) + str(self)

    def joinpath(self, *args: PATH_TYPES):
        """Appends one or more path-like objects and/or relative paths to self.

        If any path being joined is already absolute, it will override and replace self instead of join us.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object or str path):
        """
        return self._create_instance(self, *args)

    def add_suffix(self, extension: str):
        """Initialize a new path object with the added extension. Similar to with_suffix, but doesn't replace existing extensions."""
        if not isinstance(extension, str):
            return NotImplemented
        if not extension.startswith("."):
            extension = f".{extension}"
        return self.__class__(str(self) + extension)

    def endswith(self, text: str | tuple[str, ...], case_sensitive: bool = False) -> bool:
        # If case sensitivity is not required, normalize the self string and the text to lower case
        if not case_sensitive:
            self_str = str(self).lower()

            # Normalize each string in the tuple if text is a tuple
            if isinstance(text, tuple):
                text = tuple(subtext.lower() for subtext in text)
            else:
                text = text.lower()
        else:
            self_str = str(self)

        # Utilize Python's built-in endswith method
        return self_str.endswith(text)


    @staticmethod
    def _fix_path_formatting(str_path: str, slash=os.sep) -> str:
        if slash not in ("\\", "/"):
            msg = f"Invalid slash str: '{slash}'"
            raise ValueError(msg)

        formatted_path: str = str_path.strip('"')
        if not formatted_path.strip():
            return formatted_path

        # For Windows paths
        if slash == "\\":
            # Fix mixed slashes, replacing all forwardslashes with backslashes
            formatted_path = formatted_path.replace("/", "\\")
            # Replace 3 or more leading slashes with two backslashes
            formatted_path = re.sub(r"^\\{3,}", r"\\\\", formatted_path)
            # Replace repeating non-leading slashes with a single backslash
            formatted_path = re.sub(r"(?<!^)\\+", r"\\", formatted_path)
        # For Unix-like paths
        elif slash == "/":
            # Fix mixed slashes, replacing all backslashes with forwardslashes
            formatted_path = formatted_path.replace("\\", "/")
            # Replace multiple forwardslash's with a single forwardslash
            formatted_path = re.sub(r"/{2,}", "/", formatted_path)

        # Strip any trailing slashes, don't call rstrip if the formatted path == "/"
        return formatted_path if len(formatted_path) == 1 else formatted_path.rstrip(slash)

class PurePath(BasePurePath, pathlib.PurePath):
    # pylint: disable-all
    _flavour = pathlib.PureWindowsPath._flavour if os.name == "nt" else pathlib.PurePosixPath._flavour  # type: ignore[attr-defined]


class PurePosixPath(BasePurePath, pathlib.PurePosixPath):
    pass


class PureWindowsPath(BasePurePath, pathlib.PureWindowsPath):
    pass

class BasePath(BasePurePath):
    # Safe rglob operation
    def safe_rglob(self, pattern: str):
        if not isinstance(self, Path):
            return NotImplemented
        with contextlib.suppress(Exception):
            yield from self.rglob(pattern)

    # Safe iterdir operation
    def safe_iterdir(self):
        if not isinstance(self, Path):
            return NotImplemented
        with contextlib.suppress(Exception):
            yield from self.iterdir()

    # Safe is_dir operation
    def safe_isdir(self) -> bool:
        if not isinstance(self, Path):
            return NotImplemented
        try:
            return self.is_dir()
        except Exception:  # noqa: BLE001
            return False

    # Safe is_file operation
    def safe_isfile(self) -> bool:
        if not isinstance(self, Path):
            return NotImplemented
        try:
            return self.is_file()
        except Exception:  # noqa: BLE001
            return False

    # Safe exists operation
    def safe_exists(self) -> bool:
        if not isinstance(self, Path):
            return NotImplemented
        try:
            return self.exists()
        except Exception:  # noqa: BLE001
            return False

    # Safe stat operation
    def safe_stat(self, *args, **kwargs):
        if not isinstance(self, Path):
            return NotImplemented
        try:
            return self.stat(*args, **kwargs)
        except Exception:  # noqa: BLE001
            return None

    # Safe open operation
    def safe_open(self, *args, **kwargs):
        if not isinstance(self, Path):
            return NotImplemented
        try:
            return self.open(*args, **kwargs)
        except Exception:  # noqa: BLE001
            return None

    def has_access(self, recurse=False) -> bool:
        """Check if we have access to the path.

        Args:
        ----
            recurse (bool): check access for all files inside of self. Only valid if self is a folder (default is False)

        Returns:
        -------
            True if path can be modified, False otherwise.
        """
        if not isinstance(self, Path):
            return NotImplemented
        try:
            path_obj = Path(self)  # prevents usage of CaseAwarePath's wrappers
            if path_obj.is_dir():  # sourcery skip: extract-method
                test_path: Path = path_obj / f"temp_test_file_{uuid.uuid4().hex}.tmp"
                with test_path.open("w") as f:
                    f.write("test")
                test_path.unlink()
                success = True
                if recurse:
                    for f in path_obj.rglob("*"):
                        success &= f.has_access()
                return success
            if path_obj.is_file():
                return os.access(path_obj, os.R_OK) and os.access(path_obj, os.W_OK)
        except Exception:  # noqa: BLE001
            return False
        return False

    def gain_access(self, mode=0o777, owner_uid=-1, owner_gid=-1, recurse=True):
        if not isinstance(self, Path):
            return NotImplemented
        path_obj = Path(self)  # prevents usage of CaseAwarePath's wrappers
        # (Unix) Gain ownership of the folder
        if os.name != "nt" and (owner_uid != -1 or owner_gid != -1) and not path_obj.has_access():
            try:
                os.chown(path_obj, owner_uid, owner_gid)
            except Exception as e:  # noqa: BLE001
                print(f"Error during chown for {path_obj!s}: {e}")

        # chmod the folder
        if not path_obj.has_access():
            try:
                path_obj.chmod(mode)
            except Exception as e:  # noqa: BLE001
                print(f"Error during chmod for {path_obj!s}: {e}")

        # TODO: prompt the user and gain access with os-native methods.
        if not path_obj.has_access():
            try:
                if platform.system() == "Darwin":
                    path_obj.request_mac_permission()
                elif sys.platform == "Linux":
                    path_obj.request_linux_permission()
                elif sys.platform == "Windows":
                    path_obj.request_windows_permission()

            except Exception as e:  # noqa: BLE001
                print(f"Error during platform-specific permission request for {path_obj!s}: {e}")

        success: bool = path_obj.has_access()
        try:
            if recurse and path_obj.is_dir():
                for child in path_obj.iterdir():
                    success &= child.gain_access(mode, owner_uid, owner_gid)
        except Exception as e:  # noqa: BLE001
            print(f"Error gaining access for children of {path_obj!s}: {e}")
            success = False

        return success


class Path(BasePath, pathlib.Path):
    # pylint: disable-all
    _flavour = getattr(pathlib.PureWindowsPath, "_flavour", None) if os.name == "nt" else getattr(pathlib.PurePosixPath, "_flavour", None)  # type: ignore[attr-defined]


class PosixPath(BasePath, pathlib.PosixPath):
    pass


class WindowsPath(BasePath, pathlib.WindowsPath):
    pass


class CaseAwarePath(Path):
    def resolve(self, strict=False):
        new_path = super().resolve(strict)
        if self.__class__.should_resolve_case(new_path):
            new_path = self.__class__._get_case_sensitive_path(new_path)
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
            else super(self.__class__, self.__class__._get_case_sensitive_path(self)).__str__()
        )

    @staticmethod
    def _get_case_sensitive_path(path: os.PathLike | str) -> CaseAwarePath:
        pathlib_path: pathlib.Path = pathlib.Path(path)
        parts = list(pathlib_path.parts)

        for i in range(1, len(parts)):  # ignore the root (/, C:\\, etc)
            base_path: Path = Path(*parts[:i])
            next_path: Path = Path(*parts[: i + 1])

            # Find the first non-existent case-sensitive file/folder in hierarchy
            if not next_path.safe_isdir() and base_path.safe_isdir():
                base_path_items_generator = (item for item in base_path.safe_iterdir() if (i == len(parts) - 1) or item.safe_isdir())

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
    def _find_closest_match(cls, target, candidates: Generator[Path, None, None]) -> str:
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
    CaseAwarePath = Path  # type: ignore[assignment, misc]


def resolve_reg_key_to_path(reg_key: str, keystr: str):
    import winreg

    try:
        root, subkey = reg_key.split("\\", 1)
        root_key = getattr(winreg, root)
        with winreg.OpenKey(root_key, subkey) as key:
            resolved_path, _ = winreg.QueryValueEx(key, keystr)
            return resolved_path
    except (FileNotFoundError, PermissionError):
        return None


KOTOR1RegOptions = [
    (r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 32370", "InstallLocation"),
    (r"HKEY_LOCAL_MACHINE\SOFTWARE\GOG.com\Games\1207666283", "PATH"),
    (r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\GOG.com\Games\1207666283", "PATH"),
    (r"HKEY_LOCAL_MACHINE\SOFTWARE\BioWare\SW\KOTOR", "Path"),
    (r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\BioWare\SW\KOTOR", "Path"),
]

KOTOR2RegOptions = [
    (r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 208580", "InstallLocation"),
    (r"HKEY_LOCAL_MACHINE\SOFTWARE\GOG.com\Games\1421404581", "PATH"),
    (r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\GOG.com\Games\1421404581", "PATH"),
    (r"HKEY_LOCAL_MACHINE\SOFTWARE\LucasArts\KotOR2", "Path"),
    (r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\LucasArts\KotOR2", "Path"),
]

def get_default_game_paths():
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

def locate_game_paths() -> dict[Game, list[CaseAwarePath]]:
    from pykotor.common.misc import Game

    os_str = platform.system()

    # Build hardcoded default kotor locations
    raw_locations: dict[str, dict[Game, list[str]]] = get_default_game_paths()
    locations = {
        game: {case_path for case_path in (CaseAwarePath(path) for path in paths) if case_path.exists()}
        for game, paths in raw_locations.get(os_str, {}).items()
    }

    # Build kotor locations by registry (if on windows)
    if os_str == "Windows":
        for game_option, reg_options in ((Game.K1, KOTOR1RegOptions), (Game.K2, KOTOR2RegOptions)):
            for reg_key, reg_valname in reg_options:
                path_str = resolve_reg_key_to_path(reg_key, reg_valname)
                path = CaseAwarePath(path_str).resolve() if path_str else None
                if path and path.name and path.exists():
                    locations[game_option].add(path)

    locations[Game.K1] = [*locations[Game.K1]]  # type: ignore[assignment]
    locations[Game.K2] = [*locations[Game.K2]]  # type: ignore[assignment]
    return locations  # type: ignore[return-value]
