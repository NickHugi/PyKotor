
from __future__ import annotations

import os

from qtpy.QtCore import QDateTime, QFileDevice, QFileInfo  # noqa: E402
from qtpy.QtGui import QIcon


class PyQExtendedInformation(QFileInfo):
    Dir, File, System = range(3)

    def __init__(self, info=None):
        self.mFileInfo: QFileInfo = QFileInfo() if info is None else QFileInfo(info)
        self.displayType: str = ""
        self.icon: QIcon = QIcon()

    def isDir(self) -> bool:
        return self.type() == PyQExtendedInformation.Dir

    def isFile(self) -> bool:
        return self.type() == PyQExtendedInformation.File

    def isSystem(self) -> bool:
        return self.type() == PyQExtendedInformation.System

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PyQExtendedInformation):
            return False
        return (self.mFileInfo == other.mFileInfo and
                self.displayType == other.displayType and
                self.permissions() == other.permissions() and
                self.lastModified() == other.lastModified())

    def fileInfo(self) -> QFileInfo:
        return self.mFileInfo

    def isCaseSensitive(self) -> bool:
        return os.name == "posix"

    def permissions(self) -> QFileDevice.Permissions | int:
        r1 = self.mFileInfo.permissions()
        return QFileDevice.Permissions() if r1 is None else r1

    def type(self):
        if self.mFileInfo.isDir():
            return PyQExtendedInformation.Dir
        if self.mFileInfo.isFile():
            return PyQExtendedInformation.File
        if not self.mFileInfo.exists() and self.mFileInfo.isSymLink():
            return PyQExtendedInformation.System
        return PyQExtendedInformation.System

    def isSymLink(self, ignoreNtfsSymLinks: bool = False) -> bool:  # noqa: N803, FBT002, FBT001
        return (
            self.mFileInfo.suffix().strip().lower() != ".lnk"
            if ignoreNtfsSymLinks and os.name == "nt"
            else self.mFileInfo.isSymLink()
        )

    def isHidden(self) -> bool:
        return self.mFileInfo.isHidden()

    def lastModified(self) -> QDateTime:
        r1 = self.mFileInfo.lastModified()
        return QDateTime() if r1 is None else r1

    def size(self) -> int:
        size = -1
        if self.type() == PyQExtendedInformation.Dir:
            size = 0
        elif self.type() == PyQExtendedInformation.File:
            size = self.mFileInfo.size()
        elif not self.mFileInfo.exists() and not self.mFileInfo.isSymLink():
            size = -1
        return size
