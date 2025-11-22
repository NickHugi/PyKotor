from __future__ import annotations

# Try to import defusedxml, fallback to ElementTree if not available
from xml.etree import ElementTree as ET

try:  # sourcery skip: remove-redundant-exception, simplify-single-exception-tuple
    from defusedxml.ElementTree import fromstring as _fromstring

    ET.fromstring = _fromstring
except (ImportError, ModuleNotFoundError):
    print("warning: defusedxml is not available but recommended for security")

from typing import TYPE_CHECKING, Any, Callable

from loggerplus import RobustLogger
from qtpy import QtCore
from qtpy.QtWidgets import QTreeWidgetItem

if TYPE_CHECKING:
    from toolset.gui.windows.help_window import HelpWindow


class HelpContent:
    def __init__(self, help_window: HelpWindow):
        self.help_window: HelpWindow = help_window
        self.version: str | None = None

    def setup_contents(self):
        self.help_window.ui.contentsTree.clear()

        try:
            tree = ET.parse("./help/contents.xml")  # noqa: S314 incorrect warning.
            root = tree.getroot()

            self.version = str(root.get("version", "0.0"))
            self._setup_contents_rec_xml(None, root)

            # Old JSON code:
            # text = Path("./help/contents.xml").read_text()
            # data = json.loads(text)
            # self.version = data["version"]
            # self._setupContentsRecJSON(None, data)
        except Exception:  # noqa: BLE001
            RobustLogger().debug("Suppressed error in HelpWindow._setupContents", exc_info=True)

    def _setup_contents_rec_json(self, parent: QTreeWidgetItem | None, data: dict[str, Any]):
        addItem: Callable[[QTreeWidgetItem], None] = (  # type: ignore[arg-type]
            self.help_window.ui.contentsTree.addTopLevelItem
            if parent is None
            else parent.addChild
        )

        structure = data.get("structure", {})
        for title in structure:
            item = QTreeWidgetItem([title])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, structure[title]["filename"])
            addItem(item)
            self._setup_contents_rec_json(item, structure[title])

    def _setup_contents_rec_xml(self, parent: QTreeWidgetItem | None, element: ET.Element):
        addItem: Callable[[QTreeWidgetItem], None] = (  # type: ignore[arg-type]
            self.help_window.ui.contentsTree.addTopLevelItem
            if parent is None
            else parent.addChild
        )

        for child in element:
            item = QTreeWidgetItem([child.get("name", "")])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, child.get("file"))
            addItem(item)
            self._setup_contents_rec_xml(item, child)
