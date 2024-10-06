
################################################################################
## Form generated from reading UI file 'utw.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMenuBar,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from toolset.gui.widgets.edit.locstring import LocalizedStringLineEdit


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(365, 250)
        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName("actionNew")
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.actionSaveAs = QAction(MainWindow)
        self.actionSaveAs.setObjectName("actionSaveAs")
        self.actionRevert = QAction(MainWindow)
        self.actionRevert.setObjectName("actionRevert")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName("tab")
        self.verticalLayout = QVBoxLayout(self.tab)
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout_10 = QFormLayout()
        self.formLayout_10.setObjectName("formLayout_10")
        self.label_6 = QLabel(self.tab)
        self.label_6.setObjectName("label_6")

        self.formLayout_10.setWidget(0, QFormLayout.LabelRole, self.label_6)

        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName("horizontalLayout_15")
        self.nameEdit = LocalizedStringLineEdit(self.tab)
        self.nameEdit.setObjectName("nameEdit")
        self.nameEdit.setMinimumSize(QSize(0, 23))

        self.horizontalLayout_15.addWidget(self.nameEdit)


        self.formLayout_10.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout_15)

        self.label_14 = QLabel(self.tab)
        self.label_14.setObjectName("label_14")

        self.formLayout_10.setWidget(1, QFormLayout.LabelRole, self.label_14)

        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName("horizontalLayout_16")
        self.tagEdit = QLineEdit(self.tab)
        self.tagEdit.setObjectName("tagEdit")

        self.horizontalLayout_16.addWidget(self.tagEdit)

        self.tagGenerateButton = QPushButton(self.tab)
        self.tagGenerateButton.setObjectName("tagGenerateButton")
        self.tagGenerateButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout_16.addWidget(self.tagGenerateButton)


        self.formLayout_10.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout_16)

        self.label_38 = QLabel(self.tab)
        self.label_38.setObjectName("label_38")

        self.formLayout_10.setWidget(2, QFormLayout.LabelRole, self.label_38)

        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName("horizontalLayout_17")
        self.resrefEdit = QLineEdit(self.tab)
        self.resrefEdit.setObjectName("resrefEdit")
        self.resrefEdit.setMaxLength(16)

        self.horizontalLayout_17.addWidget(self.resrefEdit)

        self.resrefGenerateButton = QPushButton(self.tab)
        self.resrefGenerateButton.setObjectName("resrefGenerateButton")
        self.resrefGenerateButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout_17.addWidget(self.resrefGenerateButton)


        self.formLayout_10.setLayout(2, QFormLayout.FieldRole, self.horizontalLayout_17)


        self.verticalLayout.addLayout(self.formLayout_10)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName("tab_2")
        self.verticalLayout_2 = QVBoxLayout(self.tab_2)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.isNoteCheckbox = QCheckBox(self.tab_2)
        self.isNoteCheckbox.setObjectName("isNoteCheckbox")

        self.verticalLayout_2.addWidget(self.isNoteCheckbox)

        self.noteEnabledCheckbox = QCheckBox(self.tab_2)
        self.noteEnabledCheckbox.setObjectName("noteEnabledCheckbox")

        self.verticalLayout_2.addWidget(self.noteEnabledCheckbox)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label = QLabel(self.tab_2)
        self.label.setObjectName("label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.horizontalLayout_18 = QHBoxLayout()
        self.horizontalLayout_18.setObjectName("horizontalLayout_18")
        self.noteEdit = QLineEdit(self.tab_2)
        self.noteEdit.setObjectName("noteEdit")

        self.horizontalLayout_18.addWidget(self.noteEdit)

        self.noteChangeButton = QPushButton(self.tab_2)
        self.noteChangeButton.setObjectName("noteChangeButton")
        self.noteChangeButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout_18.addWidget(self.noteChangeButton)


        self.formLayout.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout_18)


        self.verticalLayout_2.addLayout(self.formLayout)

        self.verticalSpacer = QSpacerItem(320, 85, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.tabWidget.addTab(self.tab_2, "")
        self.commentsTab = QWidget()
        self.commentsTab.setObjectName("commentsTab")
        self.gridLayout_2 = QGridLayout(self.commentsTab)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.commentsEdit = QPlainTextEdit(self.commentsTab)
        self.commentsEdit.setObjectName("commentsEdit")

        self.gridLayout_2.addWidget(self.commentsEdit, 0, 0, 1, 1)

        self.tabWidget.addTab(self.commentsTab, "")

        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 365, 21))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
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
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", "MainWindow", None))
        self.actionNew.setText(QCoreApplication.translate("MainWindow", "New", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", "Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", "Save", None))
        self.actionSaveAs.setText(QCoreApplication.translate("MainWindow", "Save As", None))
        self.actionRevert.setText(QCoreApplication.translate("MainWindow", "Revert", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", "Exit", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", "Name:", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", "Tag:", None))
        self.tagGenerateButton.setText(QCoreApplication.translate("MainWindow", "-", None))
        self.label_38.setText(QCoreApplication.translate("MainWindow", "ResRef:", None))
        self.resrefGenerateButton.setText(QCoreApplication.translate("MainWindow", "-", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", "Basic", None))
        self.isNoteCheckbox.setText(QCoreApplication.translate("MainWindow", "Is a Map Note", None))
        self.noteEnabledCheckbox.setText(QCoreApplication.translate("MainWindow", "Map Note is Enabled", None))
        self.label.setText(QCoreApplication.translate("MainWindow", "Map Note:", None))
        self.noteChangeButton.setText(QCoreApplication.translate("MainWindow", "...", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", "Advanced", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.commentsTab), QCoreApplication.translate("MainWindow", "Comments", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", "File", None))
    # retranslateUi

