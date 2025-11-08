# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'nss.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from toolset.gui.editors.nss import CodeEditor


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName(u"actionNew")
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName(u"actionOpen")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actionSave_As = QAction(MainWindow)
        self.actionSave_As.setObjectName(u"actionSave_As")
        self.actionRevert = QAction(MainWindow)
        self.actionRevert.setObjectName(u"actionRevert")
        self.actionCompile = QAction(MainWindow)
        self.actionCompile.setObjectName(u"actionCompile")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.codeEdit = CodeEditor(self.centralwidget)
        self.codeEdit.setObjectName(u"codeEdit")
        font = QFont()
        font.setFamily(u"Courier New")
        self.codeEdit.setFont(font)
        self.codeEdit.setLineWrapMode(QPlainTextEdit.NoWrap)

        self.verticalLayout.addWidget(self.codeEdit)

        self.descriptionEdit = QPlainTextEdit(self.centralwidget)
        self.descriptionEdit.setObjectName(u"descriptionEdit")
        self.descriptionEdit.setFont(font)
        self.descriptionEdit.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.descriptionEdit.setReadOnly(True)

        self.verticalLayout.addWidget(self.descriptionEdit)

        self.verticalLayout.setStretch(0, 5)
        self.verticalLayout.setStretch(1, 3)

        self.horizontalLayout.addLayout(self.verticalLayout)

        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout_2 = QVBoxLayout(self.tab)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.functionSearchEdit = QLineEdit(self.tab)
        self.functionSearchEdit.setObjectName(u"functionSearchEdit")

        self.verticalLayout_2.addWidget(self.functionSearchEdit)

        self.functionList = QListWidget(self.tab)
        self.functionList.setObjectName(u"functionList")
        font1 = QFont()
        font1.setFamily(u"Courier New")
        font1.setPointSize(8)
        self.functionList.setFont(font1)

        self.verticalLayout_2.addWidget(self.functionList)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalLayout_3 = QVBoxLayout(self.tab_2)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.constantSearchEdit = QLineEdit(self.tab_2)
        self.constantSearchEdit.setObjectName(u"constantSearchEdit")

        self.verticalLayout_3.addWidget(self.constantSearchEdit)

        self.constantList = QListWidget(self.tab_2)
        self.constantList.setObjectName(u"constantList")
        self.constantList.setFont(font1)

        self.verticalLayout_3.addWidget(self.constantList)

        self.tabWidget.addTab(self.tab_2, "")

        self.horizontalLayout.addWidget(self.tabWidget)

        self.horizontalLayout.setStretch(0, 2)
        self.horizontalLayout.setStretch(1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSave_As)
        self.menuFile.addAction(self.actionRevert)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionCompile)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionNew.setText(QCoreApplication.translate("MainWindow", u"New", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", u"Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.actionSave_As.setText(QCoreApplication.translate("MainWindow", u"Save As", None))
        self.actionRevert.setText(QCoreApplication.translate("MainWindow", u"Revert", None))
        self.actionCompile.setText(QCoreApplication.translate("MainWindow", u"Compile", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.functionSearchEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"search...", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"Functions", None))
        self.constantSearchEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"search...", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", u"Constants", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
