
################################################################################
## Form generated from reading UI file 'utm.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMenuBar,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from toolset.gui.widgets.edit.locstring import LocalizedStringLineEdit


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(414, 335)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
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
        self.verticalLayout_3 = QVBoxLayout(self.tab)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label_6 = QLabel(self.tab)
        self.label_6.setObjectName("label_6")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_6)

        self.horizontalLayout_18 = QHBoxLayout()
        self.horizontalLayout_18.setObjectName("horizontalLayout_18")
        self.nameEdit = LocalizedStringLineEdit(self.tab)
        self.nameEdit.setObjectName("nameEdit")
        self.nameEdit.setMinimumSize(QSize(0, 23))

        self.horizontalLayout_18.addWidget(self.nameEdit)


        self.formLayout.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout_18)

        self.label_14 = QLabel(self.tab)
        self.label_14.setObjectName("label_14")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_14)

        self.horizontalLayout_19 = QHBoxLayout()
        self.horizontalLayout_19.setObjectName("horizontalLayout_19")
        self.tagEdit = QLineEdit(self.tab)
        self.tagEdit.setObjectName("tagEdit")

        self.horizontalLayout_19.addWidget(self.tagEdit)

        self.tagGenerateButton = QPushButton(self.tab)
        self.tagGenerateButton.setObjectName("tagGenerateButton")
        self.tagGenerateButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout_19.addWidget(self.tagGenerateButton)


        self.formLayout.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout_19)

        self.label_38 = QLabel(self.tab)
        self.label_38.setObjectName("label_38")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_38)

        self.horizontalLayout_20 = QHBoxLayout()
        self.horizontalLayout_20.setObjectName("horizontalLayout_20")
        self.resrefEdit = QLineEdit(self.tab)
        self.resrefEdit.setObjectName("resrefEdit")
        self.resrefEdit.setMaxLength(16)

        self.horizontalLayout_20.addWidget(self.resrefEdit)

        self.resrefGenerateButton = QPushButton(self.tab)
        self.resrefGenerateButton.setObjectName("resrefGenerateButton")
        self.resrefGenerateButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout_20.addWidget(self.resrefGenerateButton)


        self.formLayout.setLayout(2, QFormLayout.FieldRole, self.horizontalLayout_20)

        self.label_39 = QLabel(self.tab)
        self.label_39.setObjectName("label_39")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_39)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.idSpin = QSpinBox(self.tab)
        self.idSpin.setObjectName("idSpin")
        self.idSpin.setMinimum(-2147483648)
        self.idSpin.setMaximum(2147483647)

        self.horizontalLayout.addWidget(self.idSpin)

        self.horizontalSpacer_3 = QSpacerItem(29, 17, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_3)


        self.formLayout.setLayout(3, QFormLayout.FieldRole, self.horizontalLayout)


        self.verticalLayout_3.addLayout(self.formLayout)

        self.inventoryButton = QPushButton(self.tab)
        self.inventoryButton.setObjectName("inventoryButton")

        self.verticalLayout_3.addWidget(self.inventoryButton)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.groupBox = QGroupBox(self.tab)
        self.groupBox.setObjectName("groupBox")
        self.formLayout_2 = QFormLayout(self.groupBox)
        self.formLayout_2.setObjectName("formLayout_2")
        self.label = QLabel(self.groupBox)
        self.label.setObjectName("label")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label)

        self.markUpSpin = QSpinBox(self.groupBox)
        self.markUpSpin.setObjectName("markUpSpin")
        self.markUpSpin.setMaximum(1000000)

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.markUpSpin)

        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.markDownSpin = QSpinBox(self.groupBox)
        self.markDownSpin.setObjectName("markDownSpin")
        self.markDownSpin.setMaximum(1000000)

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.markDownSpin)


        self.horizontalLayout_2.addWidget(self.groupBox)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.frame_2 = QFrame(self.tab)
        self.frame_2.setObjectName("frame_2")
        self.formLayout_3 = QFormLayout(self.frame_2)
        self.formLayout_3.setObjectName("formLayout_3")
        self.label_3 = QLabel(self.frame_2)
        self.label_3.setObjectName("label_3")

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label_3)

        self.onOpenEdit = QLineEdit(self.frame_2)
        self.onOpenEdit.setObjectName("onOpenEdit")
        sizePolicy.setHeightForWidth(self.onOpenEdit.sizePolicy().hasHeightForWidth())
        self.onOpenEdit.setSizePolicy(sizePolicy)
        self.onOpenEdit.setMaxLength(16)

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.onOpenEdit)

        self.label_4 = QLabel(self.frame_2)
        self.label_4.setObjectName("label_4")

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.label_4)

        self.storeFlagSelect = QComboBox(self.frame_2)
        self.storeFlagSelect.addItem("")
        self.storeFlagSelect.addItem("")
        self.storeFlagSelect.addItem("")
        self.storeFlagSelect.setObjectName("storeFlagSelect")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.storeFlagSelect.sizePolicy().hasHeightForWidth())
        self.storeFlagSelect.setSizePolicy(sizePolicy1)

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.storeFlagSelect)


        self.verticalLayout_2.addWidget(self.frame_2, 0, Qt.AlignVCenter)


        self.horizontalLayout_2.addLayout(self.verticalLayout_2)

        self.horizontalLayout_2.setStretch(0, 1)
        self.horizontalLayout_2.setStretch(1, 2)

        self.verticalLayout_3.addLayout(self.horizontalLayout_2)

        self.tabWidget.addTab(self.tab, "")
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
        self.menubar.setGeometry(QRect(0, 0, 414, 22))
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
        self.label_39.setText(QCoreApplication.translate("MainWindow", "ID:", None))
        self.inventoryButton.setText(QCoreApplication.translate("MainWindow", "Edit Inventory", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", "Pricing", None))
        self.label.setText(QCoreApplication.translate("MainWindow", "Mark Up", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", "Mark Down", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", "OnOpenStore", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", "Store", None))
        self.storeFlagSelect.setItemText(0, QCoreApplication.translate("MainWindow", "Only Buy", None))
        self.storeFlagSelect.setItemText(1, QCoreApplication.translate("MainWindow", "Only Sell", None))
        self.storeFlagSelect.setItemText(2, QCoreApplication.translate("MainWindow", "Buy and Sell", None))

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", "Basic", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.commentsTab), QCoreApplication.translate("MainWindow", "Comments", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", "File", None))
    # retranslateUi

