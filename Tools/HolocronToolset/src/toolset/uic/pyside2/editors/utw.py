# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'utw.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from toolset.gui.widgets.edit.locstring import LocalizedStringLineEdit


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(365, 250)
        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName(u"actionNew")
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName(u"actionOpen")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actionSaveAs = QAction(MainWindow)
        self.actionSaveAs.setObjectName(u"actionSaveAs")
        self.actionRevert = QAction(MainWindow)
        self.actionRevert.setObjectName(u"actionRevert")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout = QVBoxLayout(self.tab)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout_10 = QFormLayout()
        self.formLayout_10.setObjectName(u"formLayout_10")
        self.label_6 = QLabel(self.tab)
        self.label_6.setObjectName(u"label_6")

        self.formLayout_10.setWidget(0, QFormLayout.LabelRole, self.label_6)

        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.nameEdit = LocalizedStringLineEdit(self.tab)
        self.nameEdit.setObjectName(u"nameEdit")
        self.nameEdit.setMinimumSize(QSize(0, 23))

        self.horizontalLayout_15.addWidget(self.nameEdit)


        self.formLayout_10.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout_15)

        self.label_14 = QLabel(self.tab)
        self.label_14.setObjectName(u"label_14")

        self.formLayout_10.setWidget(1, QFormLayout.LabelRole, self.label_14)

        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.tagEdit = QLineEdit(self.tab)
        self.tagEdit.setObjectName(u"tagEdit")

        self.horizontalLayout_16.addWidget(self.tagEdit)

        self.tagGenerateButton = QPushButton(self.tab)
        self.tagGenerateButton.setObjectName(u"tagGenerateButton")
        self.tagGenerateButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout_16.addWidget(self.tagGenerateButton)


        self.formLayout_10.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout_16)

        self.label_38 = QLabel(self.tab)
        self.label_38.setObjectName(u"label_38")

        self.formLayout_10.setWidget(2, QFormLayout.LabelRole, self.label_38)

        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.resrefEdit = QLineEdit(self.tab)
        self.resrefEdit.setObjectName(u"resrefEdit")
        self.resrefEdit.setMaxLength(16)

        self.horizontalLayout_17.addWidget(self.resrefEdit)

        self.resrefGenerateButton = QPushButton(self.tab)
        self.resrefGenerateButton.setObjectName(u"resrefGenerateButton")
        self.resrefGenerateButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout_17.addWidget(self.resrefGenerateButton)


        self.formLayout_10.setLayout(2, QFormLayout.FieldRole, self.horizontalLayout_17)


        self.verticalLayout.addLayout(self.formLayout_10)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalLayout_2 = QVBoxLayout(self.tab_2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.isNoteCheckbox = QCheckBox(self.tab_2)
        self.isNoteCheckbox.setObjectName(u"isNoteCheckbox")

        self.verticalLayout_2.addWidget(self.isNoteCheckbox)

        self.noteEnabledCheckbox = QCheckBox(self.tab_2)
        self.noteEnabledCheckbox.setObjectName(u"noteEnabledCheckbox")

        self.verticalLayout_2.addWidget(self.noteEnabledCheckbox)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(self.tab_2)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.horizontalLayout_18 = QHBoxLayout()
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.noteEdit = QLineEdit(self.tab_2)
        self.noteEdit.setObjectName(u"noteEdit")

        self.horizontalLayout_18.addWidget(self.noteEdit)

        self.noteChangeButton = QPushButton(self.tab_2)
        self.noteChangeButton.setObjectName(u"noteChangeButton")
        self.noteChangeButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout_18.addWidget(self.noteChangeButton)


        self.formLayout.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout_18)


        self.verticalLayout_2.addLayout(self.formLayout)

        self.verticalSpacer = QSpacerItem(320, 85, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.tabWidget.addTab(self.tab_2, "")
        self.commentsTab = QWidget()
        self.commentsTab.setObjectName(u"commentsTab")
        self.gridLayout_2 = QGridLayout(self.commentsTab)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.commentsEdit = QPlainTextEdit(self.commentsTab)
        self.commentsEdit.setObjectName(u"commentsEdit")

        self.gridLayout_2.addWidget(self.commentsEdit, 0, 0, 1, 1)

        self.tabWidget.addTab(self.commentsTab, "")

        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 365, 21))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSaveAs)
        self.menuFile.addAction(self.actionRevert)
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
        self.actionSaveAs.setText(QCoreApplication.translate("MainWindow", u"Save As", None))
        self.actionRevert.setText(QCoreApplication.translate("MainWindow", u"Revert", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Name:", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", u"Tag:", None))
        self.tagGenerateButton.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.label_38.setText(QCoreApplication.translate("MainWindow", u"ResRef:", None))
        self.resrefGenerateButton.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"Basic", None))
        self.isNoteCheckbox.setText(QCoreApplication.translate("MainWindow", u"Is a Map Note", None))
        self.noteEnabledCheckbox.setText(QCoreApplication.translate("MainWindow", u"Map Note is Enabled", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Map Note:", None))
        self.noteChangeButton.setText(QCoreApplication.translate("MainWindow", u"...", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", u"Advanced", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.commentsTab), QCoreApplication.translate("MainWindow", u"Comments", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
