# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'indoor_builder.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QMainWindow, QMenu, QMenuBar, QSizePolicy,
    QStatusBar, QVBoxLayout, QWidget)

from toolset.gui.windows.indoor_builder import IndoorMapRenderer

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName(u"actionOpen")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actionSaveAs = QAction(MainWindow)
        self.actionSaveAs.setObjectName(u"actionSaveAs")
        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName(u"actionNew")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        self.actionBuild = QAction(MainWindow)
        self.actionBuild.setObjectName(u"actionBuild")
        self.actionSettings = QAction(MainWindow)
        self.actionSettings.setObjectName(u"actionSettings")
        self.actionDeleteSelected = QAction(MainWindow)
        self.actionDeleteSelected.setObjectName(u"actionDeleteSelected")
        self.actionDownloadKits = QAction(MainWindow)
        self.actionDownloadKits.setObjectName(u"actionDownloadKits")
        self.actionInstructions = QAction(MainWindow)
        self.actionInstructions.setObjectName(u"actionInstructions")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.kitSelect = QComboBox(self.centralwidget)
        self.kitSelect.setObjectName(u"kitSelect")

        self.verticalLayout.addWidget(self.kitSelect)

        self.componentList = QListWidget(self.centralwidget)
        self.componentList.setObjectName(u"componentList")

        self.verticalLayout.addWidget(self.componentList)

        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout = QGridLayout(self.groupBox)
        self.gridLayout.setObjectName(u"gridLayout")
        self.componentImage = QLabel(self.groupBox)
        self.componentImage.setObjectName(u"componentImage")
        self.componentImage.setMinimumSize(QSize(128, 128))
        self.componentImage.setMaximumSize(QSize(128, 128))
        self.componentImage.setScaledContents(True)

        self.gridLayout.addWidget(self.componentImage, 0, 0, 1, 1)


        self.verticalLayout.addWidget(self.groupBox)


        self.horizontalLayout.addLayout(self.verticalLayout)

        self.mapRenderer = IndoorMapRenderer(self.centralwidget)
        self.mapRenderer.setObjectName(u"mapRenderer")
        self.mapRenderer.setMouseTracking(True)
        self.mapRenderer.setFocusPolicy(Qt.StrongFocus)
        self.mapRenderer.setContextMenuPolicy(Qt.CustomContextMenu)

        self.horizontalLayout.addWidget(self.mapRenderer)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 3)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 22))
        self.menuNew = QMenu(self.menubar)
        self.menuNew.setObjectName(u"menuNew")
        self.menuEdit = QMenu(self.menubar)
        self.menuEdit.setObjectName(u"menuEdit")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
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
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Map Builder", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", u"Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.actionSaveAs.setText(QCoreApplication.translate("MainWindow", u"Save As", None))
        self.actionNew.setText(QCoreApplication.translate("MainWindow", u"New", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.actionBuild.setText(QCoreApplication.translate("MainWindow", u"Build", None))
        self.actionSettings.setText(QCoreApplication.translate("MainWindow", u"Settings", None))
        self.actionDeleteSelected.setText(QCoreApplication.translate("MainWindow", u"Delete Selected", None))
        self.actionDownloadKits.setText(QCoreApplication.translate("MainWindow", u"Download Kits", None))
        self.actionInstructions.setText(QCoreApplication.translate("MainWindow", u"Instructions", None))
        self.groupBox.setTitle("")
        self.componentImage.setText("")
        self.menuNew.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuEdit.setTitle(QCoreApplication.translate("MainWindow", u"Edit", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside6
