
################################################################################
## Form generated from reading UI file 'txt.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import QGridLayout, QMenu, QMenuBar, QPlainTextEdit, QWidget


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(432, 306)
        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName("actionNew")
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.actionSave_As = QAction(MainWindow)
        self.actionSave_As.setObjectName("actionSave_As")
        self.actionRevert = QAction(MainWindow)
        self.actionRevert.setObjectName("actionRevert")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionWord_Wrap = QAction(MainWindow)
        self.actionWord_Wrap.setObjectName("actionWord_Wrap")
        self.actionWord_Wrap.setCheckable(True)
        self.actionWord_Wrap.setChecked(False)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.textEdit = QPlainTextEdit(self.centralwidget)
        self.textEdit.setObjectName("textEdit")
        font = QFont()
        font.setFamilies(["Courier New"])
        self.textEdit.setFont(font)
        self.textEdit.setLineWrapMode(QPlainTextEdit.NoWrap)

        self.gridLayout.addWidget(self.textEdit, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 432, 21))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuFormat = QMenu(self.menubar)
        self.menuFormat.setObjectName("menuFormat")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuFormat.menuAction())
        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSave_As)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionRevert)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuFormat.addAction(self.actionWord_Wrap)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", "MainWindow", None))
        self.actionNew.setText(QCoreApplication.translate("MainWindow", "New", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", "Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", "Save", None))
        self.actionSave_As.setText(QCoreApplication.translate("MainWindow", "Save As", None))
        self.actionRevert.setText(QCoreApplication.translate("MainWindow", "Revert", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", "Exit", None))
        self.actionWord_Wrap.setText(QCoreApplication.translate("MainWindow", "Word Wrap", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", "File", None))
        self.menuFormat.setTitle(QCoreApplication.translate("MainWindow", "View", None))
    # retranslateUi

