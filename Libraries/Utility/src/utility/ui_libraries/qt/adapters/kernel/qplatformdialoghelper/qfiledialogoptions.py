from __future__ import annotations

from qtpy.QtCore import QDir

from utility.ui_libraries.qt.adapters.kernel.qplatformdialoghelper.qplatformdialoghelper import AcceptMode, FileMode, ViewMode


class QFileDialogOptions:
    def __init__(self):
        self._mime_type_filters: list[str] = []
        self._name_filters: list[str] = []
        self._selected_name_filter: str = ""
        self._selected_mime_type_filter: str = ""
        self._file_mode: FileMode = FileMode.AnyFile
        self._accept_mode: AcceptMode = AcceptMode.AcceptOpen
        self._view_mode: ViewMode = ViewMode.Detail
        self._supported_schemes: list[str] = ["file"]
        self._default_suffix: str = ""
        self._filter: int = QDir.Filter(0)  # Placeholder for QDir.Filter

    def setMimeTypeFilters(self, filters: list[str]) -> None:
        self._mime_type_filters = filters

    def mimeTypeFilters(self) -> list[str]:
        return self._mime_type_filters

    def setNameFilters(self, filters: list[str]) -> None:
        self._name_filters = filters

    def nameFilters(self) -> list[str]:
        return self._name_filters

    def selectNameFilter(self, filter: str) -> None:  # noqa: A002
        if filter in self._name_filters:
            self._selected_name_filter = filter

    def selectedNameFilter(self) -> str:
        return self._selected_name_filter

    def selectMimeTypeFilter(self, filter: str) -> None:  # noqa: A002
        if filter in self._mime_type_filters:
            self._selected_mime_type_filter = filter

    def selectedMimeTypeFilter(self) -> str:
        return self._selected_mime_type_filter

    def setFileMode(self, mode: FileMode) -> None:
        self._file_mode = mode

    def fileMode(self) -> FileMode:
        return self._file_mode

    def setAcceptMode(self, mode: AcceptMode) -> None:
        self._accept_mode = mode

    def acceptMode(self) -> AcceptMode:
        return self._accept_mode

    def setViewMode(self, mode: ViewMode) -> None:
        self._view_mode = mode

    def viewMode(self) -> ViewMode:
        return self._view_mode

    def setSupportedSchemes(self, schemes: list[str]) -> None:
        self._supported_schemes = schemes

    def supportedSchemes(self) -> list[str]:
        return self._supported_schemes

    def setDefaultSuffix(self, suffix: str) -> None:
        self._default_suffix = suffix

    def defaultSuffix(self) -> str:
        return self._default_suffix

    def setFilter(self, filter: int) -> None:  # noqa: A002
        self._filter = filter

    def filter(self) -> int:
        return self._filter