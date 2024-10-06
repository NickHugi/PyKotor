
################################################################################
## Form generated from reading UI file 'utt.ui'
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
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
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
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from toolset.gui.widgets.edit.combobox_2da import ComboBox2DA
from toolset.gui.widgets.edit.locstring import LocalizedStringLineEdit
from utility.ui_libraries.qt.widgets.widgets.combobox import FilterComboBox


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(364, 296)
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

        self.label_2 = QLabel(self.tab)
        self.label_2.setObjectName("label_2")

        self.formLayout_10.setWidget(3, QFormLayout.LabelRole, self.label_2)

        self.typeSelect = QComboBox(self.tab)
        self.typeSelect.addItem("")
        self.typeSelect.addItem("")
        self.typeSelect.addItem("")
        self.typeSelect.setObjectName("typeSelect")

        self.formLayout_10.setWidget(3, QFormLayout.FieldRole, self.typeSelect)

        self.label_3 = QLabel(self.tab)
        self.label_3.setObjectName("label_3")

        self.formLayout_10.setWidget(4, QFormLayout.LabelRole, self.label_3)

        self.cursorSelect = ComboBox2DA(self.tab)
        self.cursorSelect.setObjectName("cursorSelect")

        self.formLayout_10.setWidget(4, QFormLayout.FieldRole, self.cursorSelect)


        self.verticalLayout.addLayout(self.formLayout_10)

        self.tabWidget.addTab(self.tab, "")
        self.tab_5 = QWidget()
        self.tab_5.setObjectName("tab_5")
        self.verticalLayout_4 = QVBoxLayout(self.tab_5)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.autoRemoveKeyCheckbox = QCheckBox(self.tab_5)
        self.autoRemoveKeyCheckbox.setObjectName("autoRemoveKeyCheckbox")

        self.verticalLayout_4.addWidget(self.autoRemoveKeyCheckbox)

        self.formLayout_4 = QFormLayout()
        self.formLayout_4.setObjectName("formLayout_4")
        self.label_8 = QLabel(self.tab_5)
        self.label_8.setObjectName("label_8")

        self.formLayout_4.setWidget(0, QFormLayout.LabelRole, self.label_8)

        self.keyEdit = QLineEdit(self.tab_5)
        self.keyEdit.setObjectName("keyEdit")

        self.formLayout_4.setWidget(0, QFormLayout.FieldRole, self.keyEdit)


        self.verticalLayout_4.addLayout(self.formLayout_4)

        self.line = QFrame(self.tab_5)
        self.line.setObjectName("line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_4.addWidget(self.line)

        self.formLayout_3 = QFormLayout()
        self.formLayout_3.setObjectName("formLayout_3")
        self.label = QLabel(self.tab_5)
        self.label.setObjectName("label")

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label)

        self.factionSelect = ComboBox2DA(self.tab_5)
        self.factionSelect.setObjectName("factionSelect")

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.factionSelect)

        self.highlightHeightSpin = QDoubleSpinBox(self.tab_5)
        self.highlightHeightSpin.setObjectName("highlightHeightSpin")

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.highlightHeightSpin)

        self.label_7 = QLabel(self.tab_5)
        self.label_7.setObjectName("label_7")

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.label_7)


        self.verticalLayout_4.addLayout(self.formLayout_3)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_2)

        self.tabWidget.addTab(self.tab_5, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName("tab_2")
        self.verticalLayout_3 = QVBoxLayout(self.tab_2)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.isTrapCheckbox = QCheckBox(self.tab_2)
        self.isTrapCheckbox.setObjectName("isTrapCheckbox")

        self.verticalLayout_2.addWidget(self.isTrapCheckbox)

        self.activateOnceCheckbox = QCheckBox(self.tab_2)
        self.activateOnceCheckbox.setObjectName("activateOnceCheckbox")

        self.verticalLayout_2.addWidget(self.activateOnceCheckbox)

        self.formLayout_6 = QFormLayout()
        self.formLayout_6.setObjectName("formLayout_6")
        self.label_17 = QLabel(self.tab_2)
        self.label_17.setObjectName("label_17")

        self.formLayout_6.setWidget(0, QFormLayout.LabelRole, self.label_17)

        self.trapSelect = ComboBox2DA(self.tab_2)
        self.trapSelect.setObjectName("trapSelect")

        self.formLayout_6.setWidget(0, QFormLayout.FieldRole, self.trapSelect)


        self.verticalLayout_2.addLayout(self.formLayout_6)


        self.verticalLayout_3.addLayout(self.verticalLayout_2)

        self.detectableCheckbox = QCheckBox(self.tab_2)
        self.detectableCheckbox.setObjectName("detectableCheckbox")

        self.verticalLayout_3.addWidget(self.detectableCheckbox)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label_4 = QLabel(self.tab_2)
        self.label_4.setObjectName("label_4")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_4)

        self.detectDcSpin = QSpinBox(self.tab_2)
        self.detectDcSpin.setObjectName("detectDcSpin")
        self.detectDcSpin.setMinimum(-2147483648)
        self.detectDcSpin.setMaximum(2147483647)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.detectDcSpin)


        self.verticalLayout_3.addLayout(self.formLayout)

        self.disarmableCheckbox = QCheckBox(self.tab_2)
        self.disarmableCheckbox.setObjectName("disarmableCheckbox")

        self.verticalLayout_3.addWidget(self.disarmableCheckbox)

        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName("formLayout_2")
        self.label_5 = QLabel(self.tab_2)
        self.label_5.setObjectName("label_5")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_5)

        self.disarmDcSpin = QSpinBox(self.tab_2)
        self.disarmDcSpin.setObjectName("disarmDcSpin")
        self.disarmDcSpin.setMinimum(-2147483648)
        self.disarmDcSpin.setMaximum(2147483647)

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.disarmDcSpin)


        self.verticalLayout_3.addLayout(self.formLayout_2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.tabWidget.addTab(self.tab_2, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName("tab_4")
        self.verticalLayout_5 = QVBoxLayout(self.tab_4)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.formLayout_5 = QFormLayout()
        self.formLayout_5.setObjectName("formLayout_5")
        self.label_9 = QLabel(self.tab_4)
        self.label_9.setObjectName("label_9")

        self.formLayout_5.setWidget(4, QFormLayout.LabelRole, self.label_9)

        self.onHeartbeatSelect = FilterComboBox(self.tab_4)
        self.onHeartbeatSelect.setObjectName("onHeartbeatSelect")

        self.formLayout_5.setWidget(4, QFormLayout.FieldRole, self.onHeartbeatSelect)

        self.label_10 = QLabel(self.tab_4)
        self.label_10.setObjectName("label_10")

        self.formLayout_5.setWidget(3, QFormLayout.LabelRole, self.label_10)

        self.label_11 = QLabel(self.tab_4)
        self.label_11.setObjectName("label_11")

        self.formLayout_5.setWidget(2, QFormLayout.LabelRole, self.label_11)

        self.label_12 = QLabel(self.tab_4)
        self.label_12.setObjectName("label_12")

        self.formLayout_5.setWidget(6, QFormLayout.LabelRole, self.label_12)

        self.onExitSelect = FilterComboBox(self.tab_4)
        self.onExitSelect.setObjectName("onExitSelect")

        self.formLayout_5.setWidget(3, QFormLayout.FieldRole, self.onExitSelect)

        self.onEnterSelect = FilterComboBox(self.tab_4)
        self.onEnterSelect.setObjectName("onEnterSelect")

        self.formLayout_5.setWidget(2, QFormLayout.FieldRole, self.onEnterSelect)

        self.onUserDefinedSelect = FilterComboBox(self.tab_4)
        self.onUserDefinedSelect.setObjectName("onUserDefinedSelect")

        self.formLayout_5.setWidget(6, QFormLayout.FieldRole, self.onUserDefinedSelect)

        self.label_13 = QLabel(self.tab_4)
        self.label_13.setObjectName("label_13")

        self.formLayout_5.setWidget(0, QFormLayout.LabelRole, self.label_13)

        self.label_15 = QLabel(self.tab_4)
        self.label_15.setObjectName("label_15")

        self.formLayout_5.setWidget(1, QFormLayout.LabelRole, self.label_15)

        self.label_16 = QLabel(self.tab_4)
        self.label_16.setObjectName("label_16")

        self.formLayout_5.setWidget(5, QFormLayout.LabelRole, self.label_16)

        self.onTrapTriggeredEdit = FilterComboBox(self.tab_4)
        self.onTrapTriggeredEdit.setObjectName("onTrapTriggeredEdit")

        self.formLayout_5.setWidget(5, QFormLayout.FieldRole, self.onTrapTriggeredEdit)

        self.onDisarmEdit = FilterComboBox(self.tab_4)
        self.onDisarmEdit.setObjectName("onDisarmEdit")

        self.formLayout_5.setWidget(1, QFormLayout.FieldRole, self.onDisarmEdit)

        self.onClickEdit = FilterComboBox(self.tab_4)
        self.onClickEdit.setObjectName("onClickEdit")

        self.formLayout_5.setWidget(0, QFormLayout.FieldRole, self.onClickEdit)


        self.verticalLayout_5.addLayout(self.formLayout_5)

        self.verticalSpacer_3 = QSpacerItem(20, 26, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer_3)

        self.tabWidget.addTab(self.tab_4, "")
        self.commentsTab = QWidget()
        self.commentsTab.setObjectName("commentsTab")
        self.gridLayout_2 = QGridLayout(self.commentsTab)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.commentsEdit = QPlainTextEdit(self.commentsTab)
        self.commentsEdit.setObjectName("commentsEdit")

        self.gridLayout_2.addWidget(self.commentsEdit, 0, 0, 1, 1)

        self.tabWidget.addTab(self.commentsTab, "")

        self.gridLayout.addWidget(self.tabWidget, 0, 1, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 364, 21))
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
        self.label_2.setText(QCoreApplication.translate("MainWindow", "Type:", None))
        self.typeSelect.setItemText(0, QCoreApplication.translate("MainWindow", "Generic", None))
        self.typeSelect.setItemText(1, QCoreApplication.translate("MainWindow", "Transition", None))
        self.typeSelect.setItemText(2, QCoreApplication.translate("MainWindow", "Trap", None))

        self.label_3.setText(QCoreApplication.translate("MainWindow", "Cursor:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", "Basic", None))
        self.autoRemoveKeyCheckbox.setText(QCoreApplication.translate("MainWindow", "Auto Remove Key", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", "Key Name:", None))
        self.label.setText(QCoreApplication.translate("MainWindow", "Faction:", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", "Hightlight Height:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), QCoreApplication.translate("MainWindow", "Advanced", None))
        self.isTrapCheckbox.setText(QCoreApplication.translate("MainWindow", "Is a trap", None))
        self.activateOnceCheckbox.setText(QCoreApplication.translate("MainWindow", "Activate Once", None))
        self.label_17.setText(QCoreApplication.translate("MainWindow", "Trap Type:", None))
        self.detectableCheckbox.setText(QCoreApplication.translate("MainWindow", "Detectable", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", "Detect DC:", None))
        self.disarmableCheckbox.setText(QCoreApplication.translate("MainWindow", "Disarmable", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", "Disarm DC:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", "Trap", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", "OnHeartbeat:", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", "OnExit:", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", "OnEnter:", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", "OnUserDefined:", None))
        self.label_13.setText(QCoreApplication.translate("MainWindow", "OnClick:", None))
        self.label_15.setText(QCoreApplication.translate("MainWindow", "OnDisarm:", None))
        self.label_16.setText(QCoreApplication.translate("MainWindow", "OnTrapTriggered:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QCoreApplication.translate("MainWindow", "Scripts", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.commentsTab), QCoreApplication.translate("MainWindow", "Comments", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", "File", None))
    # retranslateUi

