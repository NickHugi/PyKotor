from PyQt5.QtWidgets import QDialog, QListWidgetItem

from pykotor.extract.capsule import Capsule
from pykotor.resource.type import ResourceType


class LoadFromModuleDialog(QDialog):
    """LoadFromModuleDialog lets the user select a resource from a ERF or RIM."""

    def __init__(self, capsule: Capsule, supported):
        """Initialize a dialog to load resources from a capsule
        Args:
            capsule: Capsule - The capsule to load resources from
            supported: list - Supported resource types
        Returns:
            None: Initializes UI elements
        - Loops through each resource in the capsule
        - Checks if the resource type is supported
        - Adds supported resources to the list widget with the filename
        - Associates the original resource with each list item.
        """
        super().__init__()

        from toolset.uic.dialogs.load_from_module import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        for resource in capsule:
            if resource.restype() not in supported:
                continue
            filename = f"{resource.resname()}.{resource.restype().extension}"
            item = QListWidgetItem(filename)
            item.resource = resource
            self.ui.resourceList.addItem(item)

    def resref(self) -> str:
        return self.ui.resourceList.currentItem().resource.resname()

    def restype(self) -> ResourceType:
        return self.ui.resourceList.currentItem().resource.restype()

    def data(self) -> bytes:
        return self.ui.resourceList.currentItem().resource.data()
