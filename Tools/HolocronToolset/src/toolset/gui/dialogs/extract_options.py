from __future__ import annotations

from qtpy.QtWidgets import QDialog

from toolset.uic.qtpy.dialogs.extract_options import Ui_ExtractOptionsDialog


class ExtractOptionsDialog(QDialog):
    """Dialog for configuring extraction options."""

    def __init__(self, parent=None):
        """Initialize the dialog."""
        super().__init__(parent)
        self.ui = Ui_ExtractOptionsDialog()
        self.ui.setupUi(self)

    @property
    def tpc_decompile(self) -> bool:
        """Get whether TPC decompile is enabled."""
        return self.ui.tpcDecompileCheckbox.isChecked()

    @property
    def tpc_extract_txi(self) -> bool:
        """Get whether TPC TXI extraction is enabled."""
        return self.ui.tpcTxiCheckbox.isChecked()

    @property
    def mdl_decompile(self) -> bool:
        """Get whether MDL decompile is enabled."""
        return self.ui.mdlDecompileCheckbox.isChecked()

    @property
    def mdl_extract_textures(self) -> bool:
        """Get whether MDL texture extraction is enabled."""
        return self.ui.mdlTexturesCheckbox.isChecked()