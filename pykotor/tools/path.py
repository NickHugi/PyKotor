from __future__ import annotations

import contextlib
import os
import pathlib
import platform
import re
from pathlib import (
    Path,  # type: ignore[pylance_reportGeneralTypeIssues]
    PosixPath,  # type: ignore[pylance_reportGeneralTypeIssues]
    PurePath,  # type: ignore[pylance_reportGeneralTypeIssues]
    PurePosixPath,  # type: ignore[pylance_reportGeneralTypeIssues]
    PureWindowsPath,  # type: ignore[pylance_reportGeneralTypeIssues]
    WindowsPath,  # type: ignore[pylance_reportGeneralTypeIssues]
)
from typing import Generator, List, Tuple, Union
import uuid

PathElem = Union[str, os.PathLike]
PATH_TYPES = Union[PathElem, List[PathElem], Tuple[PathElem, ...]]


def has_attr_excluding_object(cls, attr_name):
    # Exclude the built-in 'object' class
    mro_classes = [c for c in cls.mro() if c != object]

    return any(attr_name in base_class.__dict__ for base_class in mro_classes)


def is_class_or_subclass_but_not_instance(cls, target_cls):
    if cls is target_cls:
        return True
    if not hasattr(cls, "__bases__"):
        return False
    return any(is_class_or_subclass_but_not_instance(base, target_cls) for base in cls.__bases__)


def is_instance_or_subinstance(instance, target_cls):
    if hasattr(instance, "__bases__"):  # instance is a class
        return False  # if instance is a class type, always return False
    # instance is not a class
    return type(instance) is target_cls or is_class_or_subclass_but_not_instance(type(instance), target_cls)


def simple_wrapper(fn_name, wrapped_class_type):
    def wrapped(self, *args, **kwargs):
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


def create_case_insensitive_pathlib_class(cls):
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


class BasePath:
    """BasePath is a class created to fix some annoyances with pathlib, such as its refusal to resolve mixed/repeating/trailing slashes."""

    def __new__(cls, *args: PATH_TYPES, **kwargs):
        return super().__new__(cls, *cls.parse_args(*args), **kwargs)

    def __init__(self, *args, _called_from_pathlib=True):
        next_init_method_class = next(
            (cls for cls in self.__class__.mro() if "__init__" in cls.__dict__ and cls is not BasePath),
            self.__class__,  # reminder: self.__class__ will never be BasePath
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

    def __add__(self, key: PathElem):
        """Appends a path part with the addition operator '+'.
        This method is called when the left side is self.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object or str path):
        """
        return self._create_instance(self, key)

    def __radd__(self, key: PathElem):
        """Appends a path part with the addition operator '+'.
        This method is called when the right side is self.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object or str path):
        """
        return self._create_instance(key, self)

    def joinpath(self, *args: PATH_TYPES):
        """Appends one or more path-like objects and/or relative paths to self.

        If any path being joined is already absolute, it will override and replace self instead of join us.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object or str path):
        """
        return self._create_instance(self, *args)

    def endswith(self, *text: str, case_sensitive=False) -> bool:
        if case_sensitive:
            return str(self).endswith(text)
        return str(self).lower().endswith(tuple(t.lower() for t in text))

    @staticmethod
    def _fix_path_formatting(str_path: str, slash=os.sep) -> str:
        if slash not in ("\\", "/"):
            msg = f"Invalid slash str: '{slash}'"
            raise ValueError(msg)
        if not str_path.strip():
            return str_path

        formatted_path: str = str_path.strip('"')

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


class PurePath(BasePath, PurePath):
    _flavour = PureWindowsPath._flavour if os.name == "nt" else PurePosixPath._flavour  # type: ignore pylint: disable-all


class PurePosixPath(BasePath, PurePosixPath):
    pass


class PureWindowsPath(BasePath, PureWindowsPath):
    pass


class Path(BasePath, Path):
    _flavour = PureWindowsPath._flavour if os.name == "nt" else PurePosixPath._flavour  # type: ignore pylint: disable-all
    
    # Safe rglob operation
    def safe_rglob(self, pattern: str):
        with contextlib.suppress(PermissionError, IOError, OSError, FileNotFoundError, IsADirectoryError):
            yield from self.rglob(pattern)

    # Safe iterdir operation
    def safe_iterdir(self):
        with contextlib.suppress(PermissionError, IOError, OSError, FileNotFoundError, IsADirectoryError):
            yield from self.iterdir()

    # Safe is_dir operation
    def safe_isdir(self):
        try:
            return self.is_dir()
        except Exception:
            return False

    # Safe is_file operation
    def safe_isfile(self):
        try:
            return self.is_file()
        except Exception:
            return False

    # Safe exists operation
    def safe_exists(self):
        try:
            return self.exists()
        except Exception:
            return False
    
    # Safe stat operation
    def safe_stat(self, *args, **kwargs):
        try:
            return self.stat(*args, **kwargs)
        except Exception:
            return None
    
    # Safe open operation
    def safe_open(self, *args, **kwargs):
        try:
            return self.open(*args, **kwargs)
        except Exception:
            return None

    def has_access(self, recurse=False) -> bool:
        """
        Check if we have access to the path.
        :param path: The pathlib.Path object to check (can be a file or a folder)
        :return: True if path can be modified, False otherwise.
        """
        try:
            path_obj = Path(self)
            if path_obj.is_dir():
                test_path = path_obj / f"temp_test_file_{uuid.uuid4().hex}.tmp"
                with test_path.open('w') as f:
                    f.write("test")
                test_path.unlink()
                success = True
                if recurse:
                    for f in path_obj.rglob("*"):
                        success &= f.has_access()
                return success
            if path_obj.is_file():
                access =  os.access(path_obj, os.R_OK) and os.access(path_obj, os.W_OK)
                return access
            return False
        except:
            return False

    def gain_access(self, mode=0o755, owner_uid=-1, owner_gid=-1):
        success = True

        try:
            if not self.has_access():
                if owner_uid != -1 or owner_gid != -1 and os.name != "nt":
                    os.chown(self, owner_uid, owner_gid)
            if self.has_access():
                return True

        except Exception as e:
            print(f"Error during chown for {self!s}: {e}")
            success = False

        try:
            if not self.has_access():
                self.chmod(mode)
            if self.has_access():
                return True

        except Exception as e:
            print(f"Error during chmod for {self!s}: {e}")
            success = False

        try:
            if not self.has_access():
                # TODO: prompt the user for access with os-native methods.
                if platform.system() == "Darwin":
                    self.request_mac_permission()
                elif sys.platform == "Linux":
                    self.request_linux_permission()
                elif sys.platform == "Windows":
                    self.request_windows_permission()

        except Exception as e:
            print(f"Error during platform-specific permission request for {self!s}: {e}")
            success = False

        # If directory, recurse into it
        if self.safe_isdir():
            for child in self.safe_iterdir():
                child_success = child.gain_access(mode, owner_uid, owner_gid)
                success = success and child_success

        return success


class PosixPath(BasePath, PosixPath):
    pass


class WindowsPath(BasePath, WindowsPath):
    pass


class CaseAwarePath(Path):
    def resolve(self, strict=False):
        new_path = super().resolve(strict)
        if self.__class__.should_resolve_case(new_path):
            new_path = self.__class__._get_case_sensitive_path(new_path)
        return new_path

    def __hash__(self):
        """Ensures any instance of this class will be treated the same in lists etc, if they're case-insensitive matches."""
        return hash((self.__class__.__name__, super().__str__().lower()))

    def __eq__(self, other):
        """All pathlib classes that derive from PurePath are equal to this object if their paths are case-insensitive equivalents."""
        return isinstance(other, pathlib.PurePath) and self._fix_path_formatting(str(other)).lower() == super().__str__().lower()

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__str__().lower()})"

    def __str__(self):
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
            elif not next_path.exists():
                return CaseAwarePath._create_instance(base_path.joinpath(*parts[i:]))

        # return a CaseAwarePath instance without infinitely recursing through the constructor
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
    def should_resolve_case(path) -> bool:
        if os.name == "nt":
            return False
        if isinstance(path, Path):
            path_obj = pathlib.Path(path)
            return path_obj.is_absolute() and not path_obj.exists()
        if isinstance(path, str):
            path_obj = pathlib.Path(path)
            return path_obj.is_absolute() and not path_obj.exists()
        return False


# HACK: fix later
if os.name == "posix":
    create_case_insensitive_pathlib_class(CaseAwarePath)
elif os.name == "nt":
    CaseAwarePath = Path  # type: ignore[pylance_reportGeneralTypeIssues]


def resolve_reg_key_to_path(reg_key, keystr):
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
    r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 32370",
    r"HKEY_LOCAL_MACHINE\SOFTWARE\GOG.com\Games\1207666283",
    r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\GOG.com\Games\1207666283",
    r"HKEY_LOCAL_MACHINE\SOFTWARE\BioWare\SW\KOTOR",
    r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\BioWare\SW\KOTOR",
]

KOTOR2RegOptions = [
    r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 208580",
    r"HKEY_LOCAL_MACHINE\SOFTWARE\GOG.com\Games\1421404581",
    r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\GOG.com\Games\1421404581",
    r"HKEY_LOCAL_MACHINE\SOFTWARE\LucasArts\KotOR2",
    r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\LucasArts\KotOR2",
]


def locate_game_path():
    from pykotor.common.misc import Game

    os_str = platform.system()

    locations = {
        "Windows": {
            Game.K1: [
                CaseAwarePath(r"C:\Program Files\Steam\steamapps\common\swkotor"),
                CaseAwarePath(r"C:\Program Files (x86)\Steam\steamapps\common\swkotor"),
                CaseAwarePath(r"C:\Program Files\LucasArts\SWKotOR"),
                CaseAwarePath(r"C:\Program Files (x86)\LucasArts\SWKotOR"),
                CaseAwarePath(r"C:\GOG Games\Star Wars - KotOR"),
            ],
            Game.K2: [
                CaseAwarePath(r"C:\Program Files\Steam\steamapps\common\Knights of the Old Republic II"),
                CaseAwarePath(r"C:\Program Files (x86)\Steam\steamapps\common\Knights of the Old Republic II"),
                CaseAwarePath(r"C:\Program Files\LucasArts\SWKotOR2"),
                CaseAwarePath(r"C:\Program Files (x86)\LucasArts\SWKotOR2"),
                CaseAwarePath(r"C:\GOG Games\Star Wars - KotOR2"),
            ],
        },
        "Darwin": {
            Game.K1: [
                CaseAwarePath(
                    "~/Library/Application Support/Steam/steamapps/common/swkotor/Knights of the Old Republic.app/Contents/Assets",
                ),
            ],
            Game.K2: [
                CaseAwarePath(
                    "~/Library/Application Support/Steam/steamapps/common/Knights of the Old Republic II/Knights of the Old Republic II.app/Contents/Assets",
                ),
            ],
        },
        "Linux": {
            Game.K1: [
                CaseAwarePath("~/.local/share/Steam/common/SteamApps/swkotor"),
                CaseAwarePath("~/.local/share/Steam/common/swkotor"),
                # wsl paths
                CaseAwarePath("/mnt/C/Program Files/Steam/steamapps/common/swkotor"),
                CaseAwarePath("/mnt/C/Program Files (x86)/Steam/steamapps/common/swkotor"),
                CaseAwarePath("/mnt/C/Program Files/LucasArts/SWKotOR"),
                CaseAwarePath("/mnt/C/Program Files (x86)/LucasArts/SWKotOR"),
                CaseAwarePath("/mnt/C/GOG Games/Star Wars - KotOR"),
            ],
            Game.K2: [
                CaseAwarePath("~/.local/share/Steam/common/SteamApps/Knights of the Old Republic II"),
                CaseAwarePath("~/.local/share/Steam/common/Knights of the Old Republic II"),
                # wsl paths
                CaseAwarePath("/mnt/C/Program Files/Steam/steamapps/common/Knights of the Old Republic II"),
                CaseAwarePath("/mnt/C/Program Files (x86)/Steam/steamapps/common/Knights of the Old Republic II"),
                CaseAwarePath("/mnt/C/Program Files/LucasArts/SWKotOR2"),
                CaseAwarePath("/mnt/C/Program Files (x86)/LucasArts/SWKotOR2"),
                CaseAwarePath("/mnt/C/GOG Games/Star Wars - KotOR2"),
            ],
        },
    }
    if os_str == "Windows":
        for regoption in KOTOR1RegOptions:
            path_str = resolve_reg_key_to_path(regoption, "InstallLocation")
            if path_str:
                path = CaseAwarePath(path_str).resolve()
                if path not in locations[os_str][Game.K1]:
                    locations[os_str][Game.K1].append(path)
            path_str = resolve_reg_key_to_path(regoption, "Path")
            if path_str:
                path = CaseAwarePath(path_str).resolve()
                if path not in locations[os_str][Game.K1]:
                    locations[os_str][Game.K1].append(path)
            path_str = resolve_reg_key_to_path(regoption, "PATH")
            if path_str:
                path = CaseAwarePath(path_str).resolve()
                if path not in locations[os_str][Game.K1]:
                    locations[os_str][Game.K1].append(path)
        for regoption in KOTOR2RegOptions:
            path_str = resolve_reg_key_to_path(regoption, "InstallLocation")
            if path_str:
                path = CaseAwarePath(path_str).resolve()
                if path not in locations[os_str][Game.K2]:
                    locations[os_str][Game.K2].append(path)
            path_str = resolve_reg_key_to_path(regoption, "Path")
            if path_str:
                path = CaseAwarePath(path_str).resolve()
                if path not in locations[os_str][Game.K2]:
                    locations[os_str][Game.K2].append(path)
            path_str = resolve_reg_key_to_path(regoption, "PATH")
            if path_str:
                path = CaseAwarePath(path_str).resolve()
                if path not in locations[os_str][Game.K2]:
                    locations[os_str][Game.K2].append(path)

    return locations[os_str]
