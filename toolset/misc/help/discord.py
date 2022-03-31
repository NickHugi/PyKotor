import sys

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QDialog, QWidget, QApplication

from misc.help import discord_ui


class DiscordDialog(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.ui = discord_ui.Ui_Dialog()
        self.ui.setupUi(self)
        self._setupSignals()

    def _setupSignals(self) -> None:
        self.ui.htButton.clicked.connect(lambda: self.openLink("https://discord.gg/s7G4uxGb"))
        self.ui.dsButton.clicked.connect(lambda: self.openLink("https://discord.com/invite/bRWyshn"))
        self.ui.kotorButton.clicked.connect(lambda: self.openLink("http://discord.gg/kotor"))

    def openLink(self, link: str) -> None:
        url = QUrl(link)
        QDesktopServices.openUrl(url)
