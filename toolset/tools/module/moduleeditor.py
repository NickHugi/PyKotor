from PyQt5.QtWidgets import QMainWindow, QWidget, QOpenGLWidget
from pykotor.common.module import Module

from data.installation import HTInstallation
from tools.module import moduleeditor_ui


class ModuleEditor(QMainWindow):
    def __init__(self, parent: QWidget, installation: HTInstallation, module: Module):
        super().__init__(parent)

        self._installation: HTInstallation = installation
        self._module: Module = module

        self.ui = moduleeditor_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupSignals()
        self._setupResourceTree()

    def _setupSignals(self) -> None:
        ...

    def _setupResourceTree(self) -> None:
        ...


class ModuleRenderer(QOpenGLWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
