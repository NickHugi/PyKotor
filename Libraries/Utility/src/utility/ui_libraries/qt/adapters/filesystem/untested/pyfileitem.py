from __future__ import annotations

import os
import pathlib
import stat
import sys

from contextlib import suppress
from datetime import datetime

import qtpy

from pykotor.tools.path import CaseAwarePath

if qtpy.API_NAME in ("PyQt6", "PySide6"):
    QDesktopWidget = None
    from qtpy.QtGui import QUndoCommand, QUndoStack  # pyright: ignore[reportPrivateImportUsage]  # noqa: F401
elif qtpy.API_NAME in ("PyQt5", "PySide2"):
    from qtpy.QtWidgets import QDesktopWidget, QUndoCommand, QUndoStack  # noqa: F401  # pyright: ignore[reportPrivateImportUsage]
else:
    raise RuntimeError(f"Unexpected qtpy version: '{qtpy.API_NAME}'")


def update_sys_path(_path: pathlib.Path):
    working_dir = str(_path)
    print("<SDM> [update_sys_path scope] working_dir: ", working_dir)

    if working_dir not in sys.path:
        sys.path.append(working_dir)


file_absolute_path = pathlib.Path(__file__).resolve()

pykotor_path = file_absolute_path.parents[6] / "Libraries" / "PyKotor" / "src" / "pykotor"
if pykotor_path.exists():
    update_sys_path(pykotor_path.parent)
pykotor_gl_path = file_absolute_path.parents[6] / "Libraries" / "PyKotorGL" / "src" / "pykotor"
if pykotor_gl_path.exists():
    update_sys_path(pykotor_gl_path.parent)
utility_path = file_absolute_path.parents[6] / "Libraries" / "Utility" / "src"
if utility_path.exists():
    update_sys_path(utility_path)
toolset_path = file_absolute_path.parents[3] / "toolset"
if toolset_path.exists():
    update_sys_path(toolset_path.parent)
    if __name__ == "__main__":
        os.chdir(toolset_path)


from typing import TYPE_CHECKING  # noqa: E402

from qtpy.QtCore import QDateTime, QFileInfo  # noqa: E402

from utility.system.path import Path  # noqa: E402

if TYPE_CHECKING:
    from qtpy.QtCore import QObject


class PyFileInfo:
    def __init__(
        self,
        file: str | Path | PyFileInfo | QFileInfo | None = None,
        folder: str | Path | None = None,
        parent: QObject | None = None,
    ):  # noqa: A002
        """Initializes the QFileInfo object."""
        self._parent = parent
        super().__init__()
        if isinstance(file, (PyFileInfo, QFileInfo)):
            self._path: Path = self._getPathType()(file.filePath())
        elif folder is not None:
            self._path = self._getPathType()(folder) / self._getPathType()(file)
        elif file is not None:
            self._path = self._getPathType()(file)
        else:
            self._path = self._getPathType()()
        self.__exists = self._path.exists()
        self._stat = None
        self._is_symlink = self._path.is_symlink()
        self._is_case_sensitive = os.name == "posix"
        if self.__exists:
            with suppress(FileNotFoundError, PermissionError):
                self._stat = self._path.stat()

    def parent(self) -> QObject:
        return self._parent

    # Initialization and Refresh Methods
    def refresh(self):
        """Refreshes the file information by re-stat'ing the file."""
        self.__exists = self._path.exists()
        self._is_symlink = self._path.is_symlink()
        if self.__exists:
            try:
                self._stat = self._path.stat()
            except (FileNotFoundError, PermissionError):
                self._stat = None
        else:
            self._stat = None

    def setCaching(self, enable: bool):
        """Placeholder method for compatibility. Caching is not implemented."""
        ...  # Caching is not implemented in this class.

    def caching(self) -> bool:
        """Returns False as caching is not implemented."""
        return False

    def setFile(self, file: str | Path | PyFileInfo | QFileInfo, dir: str | Path | None = None):  # noqa: A002
        """Sets the file _path for this object."""
        if isinstance(file, (PyFileInfo, QFileInfo)):
            self._path = self._getPathType()(file.filePath())
        elif dir is not None:
            self._path = self._getPathType()(dir) / self._getPathType()(file)
        else:
            self._path = self._getPathType()(file)
        self.refresh()

    # Path and File Name Methods
    def absoluteDir(self) -> Path:
        """Returns the absolute directory of the file."""
        return self._path.resolve().parent

    def absoluteFilePath(self) -> str:
        """Returns the absolute file _path."""
        return str(self._path.resolve())

    def absolutePath(self) -> str:
        """Returns the absolute _path without the file name."""
        return str(self._path.resolve().parent)

    def baseName(self) -> str:
        """Returns the base name of the file without extension."""
        return self._path.stem

    def completeBaseName(self) -> str:
        """Returns the complete base name including all dots except the last."""
        name = self._path.name
        parts = name.split(".")
        return ".".join(parts[:-1]) if len(parts) > 1 else name

    def completeSuffix(self) -> str:
        """Returns all suffixes of the file name."""
        name = self._path.name
        parts = name.split(".")
        return ".".join(parts[1:]) if len(parts) > 1 else ""

    def suffix(self) -> str:
        """Returns the last suffix of the file name."""
        return self._path.suffix.lstrip(".")

    def fileName(self) -> str:
        """Returns the file name with extension."""
        return self._path.name

    def filePath(self) -> str:
        """Returns the file _path (can be relative)."""
        return str(self._path)

    def canonicalFilePath(self) -> str | None:
        """Returns the canonical file _path without symbolic links."""
        try:
            return str(self._path.resolve(strict=True))
        except FileNotFoundError:
            return None

    def canonicalPath(self) -> str | None:
        """Returns the canonical _path without the file name."""
        canonical = self.canonicalFilePath()
        return str(self._getPathType()(canonical).parent) if canonical else None

    def dir(self) -> Path:
        """Returns the directory as a Path object."""
        return self._path.parent

    def exists(self) -> bool:
        """Returns True if the file exists."""
        return self.__exists

    def _getPathType(self) -> type[Path]:
        return CaseAwarePath if self.is_case_sensitive() else Path

    def is_case_sensitive(self) -> bool:
        return self._is_case_sensitive

    def isReadable(self) -> bool:
        """Returns True if the file is readable."""
        return os.access(self._path, os.R_OK)

    def isWritable(self) -> bool:
        """Returns True if the file is writable."""
        return os.access(self._path, os.W_OK)

    def isExecutable(self) -> bool:
        """Returns True if the file is executable."""
        return os.access(self._path, os.X_OK)

    def isAbsolute(self) -> bool:
        """Returns True if the _path is absolute."""
        return self._path.is_absolute()

    def isRelative(self) -> bool:
        """Returns True if the _path is relative."""
        return not self._path.is_absolute()

    def isFile(self) -> bool:
        """Returns True if the _path is a regular file."""
        return self._path.is_file()

    def isDir(self) -> bool:
        """Returns True if the _path is a directory."""
        return self._path.is_dir()

    def isSymLink(self) -> bool:
        """Returns True if the _path is a symbolic link."""
        return self._is_symlink

    def isSymbolicLink(self) -> bool:
        """Same as isSymLink()."""
        return self.isSymLink()

    def isHidden(self) -> bool:
        """Returns True if the file is hidden."""
        if sys.platform != "win32":
            return self._path.name.lstrip().lstrip("/").lstrip("\\").startswith(".")
        from ctypes import windll
        attrs = windll.kernel32.GetFileAttributesW(str(self._path))
        assert attrs != -1
        return bool(attrs & 2)

    def isBundle(self) -> bool:
        """Returns True if the file is a macOS bundle."""
        return sys.platform == "Darwin" and self._path.suffix.lower() in {".app", ".bundle", ".framework", ".plugin", ".kext"}

    def isJunction(self) -> bool:
        """Returns True if the _path is a Windows junction."""
        return self.isDir() and self.isSymLink() if os.name == "nt" else False

    def isShortcut(self) -> bool:
        """Returns True if the file is a Windows shortcut."""
        return self._path.suffix.lower() == ".lnk" and os.name == "nt"

    def isNativePath(self) -> bool:
        """Returns True if the _path uses the native _path separators."""
        return ("/" in str(self._path)) if os.sep == "/" else ("\\" in str(self._path))

    def makeAbsolute(self) -> bool:
        """Converts the _path to an absolute _path if it is not already."""
        if not self._path.is_absolute():
            self._path = self._path.resolve()
            self.refresh()
            return True
        return False

    def size(self) -> int:
        """Returns the size of the file in bytes."""
        return self._stat.st_size if self._stat else 0

    def lastModified(self) -> QDateTime | None:
        """Returns the last modification time."""
        return QDateTime.fromMSecsSinceEpoch(int(self._stat.st_mtime * 1000)) if self._stat else None  # noqa: DTZ006

    def lastRead(self) -> QDateTime | None:
        """Returns the last access time."""
        return QDateTime.fromMSecsSinceEpoch(int(self._stat.st_atime * 1000)) if self._stat else None  # noqa: DTZ006

    def birthTime(self) -> QDateTime | None:
        """Returns the creation time."""
        if self._stat:
            return QDateTime.fromMSecsSinceEpoch(
                int(
                    self._stat.st_ctime
                    if os.name == "nt"
                    else self._stat.st_birthtime * 1000
                )
            )  # noqa: DTZ006
        return None

    def metadataChangeTime(self) -> QDateTime | None:
        """Returns the metadata change time."""
        return QDateTime.fromMSecsSinceEpoch(int(self._stat.st_ctime * 1000)) if self._stat else None  # noqa: DTZ006

    def owner(self) -> str | None:
        """Returns the owner name of the file."""
        if sys.platform != "win32" and self._stat:
            with suppress(KeyError):
                import pwd
                return pwd.getpwuid(self._stat.st_uid).pw_name
        return None

    def ownerId(self) -> int | None:
        """Returns the owner ID of the file."""
        return self._stat.st_uid if self._stat else None

    def group(self) -> str | None:
        """Returns the group name of the file."""
        if sys.platform != "win32" and self._stat:
            try:
                import grp
                return grp.getgrgid(self._stat.st_gid).gr_name
            except KeyError:
                return None
        return None

    def groupId(self) -> int | None:
        """Returns the group ID of the file."""
        return None if os.name == "nt" or self._stat is None else self._stat.st_gid

    def permissions(self) -> int | None:
        """Returns the permission bits of the file."""
        return None if self._stat is None else stat.S_IMODE(self._stat.st_mode)

    def permission(self, permissions: int) -> bool:
        """Checks if the file has the specified permissions."""
        current_permissions = self.permissions()
        if current_permissions is None:
            return False
        return (current_permissions & permissions) == permissions

    def symLinkTarget(self) -> str | None:
        """Returns the target of the symbolic link."""
        if self.isSymLink():
            try:
                return str(self._path.resolve(strict=False))
            except RuntimeError:
                return None
        return None

    def fileTime(self, time_type: str) -> QDateTime | None:
        """Returns the specified file time.
        time_type can be 'birth', 'metadata', 'access', or 'modification'.
        """
        if time_type == "birth":
            return self.birthTime()
        if time_type == "metadata":
            return self.metadataChangeTime()
        if time_type == "access":
            return self.lastRead()
        if time_type == "modification":
            return self.lastModified()
        raise ValueError("Invalid time_type. Must be 'birth', 'metadata', 'access', or 'modification'.")

    def swap(self, other: QFileInfo):
        """Swaps the contents with another QFileInfo object."""
        if isinstance(other, QFileInfo):
            QFileInfo.swap(QFileInfo(other) if isinstance(other, PyFileInfo) else other)  # pyright: ignore[reportCallIssue]
        if isinstance(other, PyFileInfo):
            ...
        else:
            raise TypeError("swap() argument must be a QFileInfo")
        self._path, other._path = other._path, self._path  # noqa: SLF001
        self.refresh()
        other.refresh()

    # Comparison Operators
    def __eq__(self, other: QFileInfo) -> bool:
        """Checks if two QFileInfo objects refer to the same file."""
        if not isinstance(other, QFileInfo):
            return NotImplemented
        return self.absoluteFilePath() == other.absoluteFilePath()

    def __ne__(self, other: QFileInfo) -> bool:
        """Checks if two QFileInfo objects do not refer to the same file."""
        result = self.__eq__(other)
        return result is NotImplemented or not result

    def __repr__(self):
        return f"<QFileInfo _path='{self._path}'>"




class PyWrappedQFileInfo:
    def __init__(
        self,
        file: str | Path | None = None,
        folder: str | Path | None = None,
    ):
        if folder is not None:
            self._path = self._getPathType()(folder) / self._getPathType()(file)
        elif file is not None:
            self._path = self._getPathType()(file)
        else:
            self._path = self._getPathType()()
        self._exists = self._path.exists()
        self._stat = None
        self._is_symlink = self._path.is_symlink()
        self._is_case_sensitive: bool = os.name == "posix"
        if self._exists:
            with suppress(OSError):
                self._stat = self._path.stat()

    def refresh(self):
        """Refreshes the file information by re-stat'ing the file."""
        self._exists = self._path.exists()
        self._is_symlink = self._path.is_symlink()
        if self._exists:
            try:
                self._stat = self._path.stat()
            except OSError:
                self._stat = None
        else:
            self._stat = None

    def setFile(self, file: str | os.PathLike, dir: str | os.PathLike | None = None):  # noqa: A002
        """Sets the file path for this object."""
        file_obj = Path(file)
        if dir is None or file_obj.is_absolute():
            self._path: Path = file_obj
        else:
            self._path = self._getPathType()(dir, file)
        self._path = self._getPathType()(file) if dir is None else self._getPathType()(dir, file)
        self.refresh()

    def absoluteDir(self) -> Path:
        """Returns the absolute directory of the file."""
        return self._path.resolve().parent

    def absoluteFilePath(self) -> str:
        """Returns the absolute file path."""
        return str(self._path.resolve())

    def absolutePath(self) -> str:
        """Returns the absolute path without the file name."""
        return str(self._path.resolve().parent)

    def baseName(self) -> str:
        """Returns the base name of the file without extension."""
        return self._path.stem

    def completeBaseName(self) -> str:
        """Returns the complete base name including all dots except the last."""
        name = self._path.name
        parts = name.split(".")
        return ".".join(parts[:-1]) if len(parts) > 1 else name

    def completeSuffix(self) -> str:
        """Returns all suffixes of the file name."""
        name = self._path.name
        parts = name.split(".")
        return ".".join(parts[1:]) if len(parts) > 1 else ""

    def suffix(self) -> str:
        """Returns the last suffix of the file name."""
        return self._path.suffix.lstrip(".")

    def fileName(self) -> str:
        """Returns the file name with extension."""
        return self._path.name

    def filePath(self) -> str:
        """Returns the file path (can be relative)."""
        return str(self._path)

    def canonicalFilePath(self) -> str | None:
        """Returns the canonical file path without symbolic links."""
        try:
            return str(self._path.resolve(strict=True))
        except FileNotFoundError:
            return None

    def canonicalPath(self) -> str | None:
        """Returns the canonical path without the file name."""
        canonical = self.canonicalFilePath()
        return str(self._getPathType()(canonical).parent) if canonical else None

    def dir(self) -> Path:
        """Returns the directory as a Path object."""
        return self._path.parent

    def exists(self) -> bool:
        """Returns True if the file exists."""
        return self._exists

    def _getPathType(self) -> type[Path]:
        return CaseAwarePath if self.is_case_sensitive() else Path

    def is_case_sensitive(self) -> bool:
        return self._is_case_sensitive

    def isReadable(self) -> bool:
        """Returns True if the file is readable."""
        return os.access(self._path, os.R_OK)

    def isWritable(self) -> bool:
        """Returns True if the file is writable."""
        return os.access(self._path, os.W_OK)

    def isExecutable(self) -> bool:
        """Returns True if the file is executable."""
        return os.access(self._path, os.X_OK)

    def isAbsolute(self) -> bool:
        """Returns True if the path is absolute."""
        return self._path.is_absolute()

    def isRelative(self) -> bool:
        """Returns True if the path is relative."""
        return not self._path.is_absolute()

    def isFile(self) -> bool:
        """Returns True if the path is a regular file."""
        return self._path.is_file()

    def isDir(self) -> bool:
        """Returns True if the path is a directory."""
        return self._path.is_dir()

    def isSymLink(self) -> bool:
        """Returns True if the path is a symbolic link."""
        return self._is_symlink

    def isHidden(self) -> bool:
        """Returns True if the file is hidden."""
        if sys.platform != "win32":
            return self._path.name.lstrip().lstrip("/").lstrip("\\").startswith(".")
        with suppress(Exception):
            from ctypes import windll
            attrs = windll.kernel32.GetFileAttributesW(str(self._path))
            assert attrs != -1
            return bool(attrs & 2)
        return False

    def isBundle(self) -> bool:
        """Returns True if the file is a macOS bundle."""
        if sys.platform == "Darwin":
            return self._path.suffix.lower() in [".app", ".bundle", ".framework", ".plugin", ".kext"]
        return False

    def isJunction(self) -> bool:
        """Returns True if the path is a Windows junction."""
        return self.isDir() and self.isSymLink() if os.name == "nt" else False

    def isShortcut(self) -> bool:
        """Returns True if the file is a Windows shortcut."""
        return self._path.suffix.lower() == ".lnk" and os.name == "nt"

    def isNativePath(self) -> bool:
        """Returns True if the path uses the native path separators."""
        return ("/" in str(self._path)) if os.sep == "/" else ("\\" in str(self._path))

    def makeAbsolute(self) -> bool:
        """Converts the path to an absolute path if it is not already."""
        if not self._path.is_absolute():
            self._path = self._path.resolve()
            self.refresh()
            return True
        return False

    def size(self) -> int:
        """Returns the size of the file in bytes."""
        return self._stat.st_size if self._stat else 0

    def lastModified(self) -> datetime | None:
        """Returns the last modification time."""
        return datetime.fromtimestamp(self._stat.st_mtime) if self._stat else None  # noqa: DTZ006

    def lastRead(self) -> datetime | None:
        """Returns the last access time."""
        return datetime.fromtimestamp(self._stat.st_atime) if self._stat else None  # noqa: DTZ006

    def birthTime(self) -> datetime | None:
        """Returns the creation time."""
        if self._stat:
            return datetime.fromtimestamp(  # noqa: DTZ006
                self._stat.st_ctime
                if os.name == "nt"
                else self._stat.st_birthtime
            )
        return None

    def metadataChangeTime(self) -> datetime | None:
        """Returns the metadata change time."""
        return datetime.fromtimestamp(self._stat.st_ctime) if self._stat else None  # noqa: DTZ006

    def owner(self) -> str | None:
        """Returns the owner name of the file."""
        if sys.platform != "win32" and self._stat:
            with suppress(KeyError):
                import pwd
                return pwd.getpwuid(self._stat.st_uid).pw_name
        return None

    def ownerId(self) -> int | None:
        """Returns the owner ID of the file."""
        return self._stat.st_uid if self._stat else None

    def group(self) -> str | None:
        """Returns the group name of the file."""
        if sys.platform != "win32" and self._stat:
            try:
                import grp
                return grp.getgrgid(self._stat.st_gid).gr_name
            except KeyError:
                return None
        return None

    def groupId(self) -> int | None:
        """Returns the group ID of the file."""
        return None if os.name == "nt" or self._stat is None else self._stat.st_gid

    def permissions(self) -> int | None:
        """Returns the permission bits of the file."""
        return None if self._stat is None else stat.S_IMODE(self._stat.st_mode)

    def permission(self, permissions: int) -> bool:
        """Checks if the file has the specified permissions."""
        current_permissions = self.permissions()
        if current_permissions is None:
            return False
        return (current_permissions & permissions) == permissions

    def symLinkTarget(self) -> str | None:
        """Returns the target of the symbolic link."""
        if self.isSymLink():
            try:
                return str(self._path.resolve(strict=False))
            except RuntimeError:
                return None
        return None

    def fileTime(self, time_type: str) -> datetime | None:
        """Returns the specified file time.
        time_type can be 'birth', 'metadata', 'access', or 'modification'.
        """
        if time_type == "birth":
            return self.birthTime()
        if time_type == "metadata":
            return self.metadataChangeTime()
        if time_type == "access":
            return self.lastRead()
        if time_type == "modification":
            return self.lastModified()
        raise ValueError("Invalid time_type. Must be 'birth', 'metadata', 'access', or 'modification'.")

    def __eq__(self, other: PyFileInfo) -> bool:
        """Checks if two PyFileInfo objects refer to the same file."""
        if not isinstance(other, PyFileInfo):
            return NotImplemented
        return self.absoluteFilePath() == other.absoluteFilePath()

    def __ne__(self, other: PyFileInfo) -> bool:
        """Checks if two PyFileInfo objects do not refer to the same file."""
        result = self.__eq__(other)
        return result is NotImplemented or not result

    def __repr__(self):
        return f"<PyFileInfo path='{self._path}'>"
