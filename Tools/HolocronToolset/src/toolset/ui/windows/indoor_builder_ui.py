
################################################################################
## Form generated from reading UI file 'indoor_builder.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QListWidget, QMenu, QMenuBar, QStatusBar, QVBoxLayout, QWidget

from toolset.gui.windows.indoor_builder import IndoorMapRenderer


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.actionSaveAs = QAction(MainWindow)
        self.actionSaveAs.setObjectName("actionSaveAs")
        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName("actionNew")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionBuild = QAction(MainWindow)
        self.actionBuild.setObjectName("actionBuild")
        self.actionSettings = QAction(MainWindow)
        self.actionSettings.setObjectName("actionSettings")
        self.actionDeleteSelected = QAction(MainWindow)
        self.actionDeleteSelected.setObjectName("actionDeleteSelected")
        self.actionDownloadKits = QAction(MainWindow)
        self.actionDownloadKits.setObjectName("actionDownloadKits")
        self.actionInstructions = QAction(MainWindow)
        self.actionInstructions.setObjectName("actionInstructions")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.kitSelect = QComboBox(self.centralwidget)
        self.kitSelect.setObjectName("kitSelect")

        self.verticalLayout.addWidget(self.kitSelect)

        self.componentList = QListWidget(self.centralwidget)
        self.componentList.setObjectName("componentList")

        self.verticalLayout.addWidget(self.componentList)

        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.componentImage = QLabel(self.groupBox)
        self.componentImage.setObjectName("componentImage")
        self.componentImage.setMinimumSize(QSize(128, 128))
        self.componentImage.setMaximumSize(QSize(128, 128))
        self.componentImage.setScaledContents(True)

        self.gridLayout.addWidget(self.componentImage, 0, 0, 1, 1)


        self.verticalLayout.addWidget(self.groupBox)


        self.horizontalLayout.addLayout(self.verticalLayout)

        self.mapRenderer = IndoorMapRenderer(self.centralwidget)
        self.mapRenderer.setObjectName("mapRenderer")
        self.mapRenderer.setMouseTracking(True)
        self.mapRenderer.setFocusPolicy(Qt.StrongFocus)
        self.mapRenderer.setContextMenuPolicy(Qt.CustomContextMenu)

        self.horizontalLayout.addWidget(self.mapRenderer)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 3)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 22))
        self.menuNew = QMenu(self.menubar)
        self.menuNew.setObjectName("menuNew")
        self.menuEdit = QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuNew.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuNew.addAction(self.actionNew)
        self.menuNew.addAction(self.actionOpen)
        self.menuNew.addAction(self.actionSave)
        self.menuNew.addAction(self.actionSaveAs)
        self.menuNew.addSeparator()
        self.menuNew.addAction(self.actionBuild)
        self.menuNew.addAction(self.actionSettings)
        self.menuNew.addSeparator()
        self.menuNew.addAction(self.actionDownloadKits)
        self.menuNew.addSeparator()
        self.menuNew.addAction(self.actionExit)
        self.menuNew.addSeparator()
        self.menuEdit.addAction(self.actionDeleteSelected)
        self.menuHelp.addAction(self.actionInstructions)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", "Map Builder", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", "Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", "Save", None))
        self.actionSaveAs.setText(QCoreApplication.translate("MainWindow", "Save As", None))
        self.actionNew.setText(QCoreApplication.translate("MainWindow", "New", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", "Exit", None))
        self.actionBuild.setText(QCoreApplication.translate("MainWindow", "Build", None))
        self.actionSettings.setText(QCoreApplication.translate("MainWindow", "Settings", None))
        self.actionDeleteSelected.setText(QCoreApplication.translate("MainWindow", "Delete Selected", None))
        self.actionDownloadKits.setText(QCoreApplication.translate("MainWindow", "Download Kits", None))
        self.actionInstructions.setText(QCoreApplication.translate("MainWindow", "Instructions", None))
        self.groupBox.setTitle("")
        self.componentImage.setText("")
        self.menuNew.setTitle(QCoreApplication.translate("MainWindow", "File", None))
        self.menuEdit.setTitle(QCoreApplication.translate("MainWindow", "Edit", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", "Help", None))
    # retranslateUi

