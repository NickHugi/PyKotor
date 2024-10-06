
################################################################################
## Form generated from reading UI file 'dlg_original.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMenu,
    QMenuBar,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from toolset.gui.common.widgets.combobox import FilterComboBox
from toolset.gui.editors.dlg import DLGTreeView
from toolset.gui.widgets.edit.combobox_2da import ComboBox2DA
from toolset.gui.widgets.edit.spinbox import GFFFieldSpinBox


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1135, 647)
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
        self.actionReloadTree = QAction(MainWindow)
        self.actionReloadTree.setObjectName("actionReloadTree")
        self.actionUnfocus = QAction(MainWindow)
        self.actionUnfocus.setObjectName("actionUnfocus")
        self.actionUnfocus.setEnabled(False)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_2 = QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.splitter = QSplitter(self.centralwidget)
        self.splitter.setObjectName("splitter")
        self.splitter.setOrientation(Qt.Vertical)
        self.dialogTree = DLGTreeView(self.splitter)
        self.dialogTree.setObjectName("dialogTree")
        self.dialogTree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.dialogTree.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.dialogTree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.dialogTree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.splitter.addWidget(self.dialogTree)
        self.dialogTree.header().setVisible(False)
        self.layoutWidget = QWidget(self.splitter)
        self.layoutWidget.setObjectName("layoutWidget")
        self.horizontalLayout = QHBoxLayout(self.layoutWidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QLabel(self.layoutWidget)
        self.label.setObjectName("label")

        self.verticalLayout.addWidget(self.label)

        self.speakerEdit = QLineEdit(self.layoutWidget)
        self.speakerEdit.setObjectName("speakerEdit")

        self.verticalLayout.addWidget(self.speakerEdit)

        self.label_21 = QLabel(self.layoutWidget)
        self.label_21.setObjectName("label_21")

        self.verticalLayout.addWidget(self.label_21)

        self.listenerEdit = QLineEdit(self.layoutWidget)
        self.listenerEdit.setObjectName("listenerEdit")

        self.verticalLayout.addWidget(self.listenerEdit)

        self.label_2 = QLabel(self.layoutWidget)
        self.label_2.setObjectName("label_2")

        self.verticalLayout.addWidget(self.label_2)

        self.textEdit = QPlainTextEdit(self.layoutWidget)
        self.textEdit.setObjectName("textEdit")
        self.textEdit.setReadOnly(True)

        self.verticalLayout.addWidget(self.textEdit)


        self.horizontalLayout.addLayout(self.verticalLayout)

        self.tabWidget = QTabWidget(self.layoutWidget)
        self.tabWidget.setObjectName("tabWidget")
        self.fileTab = QWidget()
        self.fileTab.setObjectName("fileTab")
        self.horizontalLayout_11 = QHBoxLayout(self.fileTab)
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.formLayout_6 = QFormLayout()
        self.formLayout_6.setObjectName("formLayout_6")
        self.label_37 = QLabel(self.fileTab)
        self.label_37.setObjectName("label_37")

        self.formLayout_6.setWidget(0, QFormLayout.LabelRole, self.label_37)

        self.onEndEdit = FilterComboBox(self.fileTab)
        self.onEndEdit.setObjectName("onEndEdit")

        self.formLayout_6.setWidget(0, QFormLayout.FieldRole, self.onEndEdit)

        self.label_38 = QLabel(self.fileTab)
        self.label_38.setObjectName("label_38")

        self.formLayout_6.setWidget(1, QFormLayout.LabelRole, self.label_38)

        self.onAbortEdit = FilterComboBox(self.fileTab)
        self.onAbortEdit.setObjectName("onAbortEdit")

        self.formLayout_6.setWidget(1, QFormLayout.FieldRole, self.onAbortEdit)

        self.label_39 = QLabel(self.fileTab)
        self.label_39.setObjectName("label_39")

        self.formLayout_6.setWidget(2, QFormLayout.LabelRole, self.label_39)

        self.voIdEdit = QLineEdit(self.fileTab)
        self.voIdEdit.setObjectName("voIdEdit")
        self.voIdEdit.setMaxLength(16)

        self.formLayout_6.setWidget(2, QFormLayout.FieldRole, self.voIdEdit)

        self.label_40 = QLabel(self.fileTab)
        self.label_40.setObjectName("label_40")

        self.formLayout_6.setWidget(3, QFormLayout.LabelRole, self.label_40)

        self.ambientTrackEdit = QLineEdit(self.fileTab)
        self.ambientTrackEdit.setObjectName("ambientTrackEdit")
        self.ambientTrackEdit.setMaxLength(16)

        self.formLayout_6.setWidget(3, QFormLayout.FieldRole, self.ambientTrackEdit)

        self.label_41 = QLabel(self.fileTab)
        self.label_41.setObjectName("label_41")

        self.formLayout_6.setWidget(4, QFormLayout.LabelRole, self.label_41)

        self.cameraModelEdit = QLineEdit(self.fileTab)
        self.cameraModelEdit.setObjectName("cameraModelEdit")
        self.cameraModelEdit.setMaxLength(16)

        self.formLayout_6.setWidget(4, QFormLayout.FieldRole, self.cameraModelEdit)

        self.label_42 = QLabel(self.fileTab)
        self.label_42.setObjectName("label_42")

        self.formLayout_6.setWidget(5, QFormLayout.LabelRole, self.label_42)

        self.label_43 = QLabel(self.fileTab)
        self.label_43.setObjectName("label_43")

        self.formLayout_6.setWidget(6, QFormLayout.LabelRole, self.label_43)

        self.conversationSelect = QComboBox(self.fileTab)
        self.conversationSelect.addItem("")
        self.conversationSelect.addItem("")
        self.conversationSelect.addItem("")
        self.conversationSelect.addItem("")
        self.conversationSelect.addItem("")
        self.conversationSelect.setObjectName("conversationSelect")

        self.formLayout_6.setWidget(5, QFormLayout.FieldRole, self.conversationSelect)

        self.computerSelect = QComboBox(self.fileTab)
        self.computerSelect.addItem("")
        self.computerSelect.addItem("")
        self.computerSelect.setObjectName("computerSelect")

        self.formLayout_6.setWidget(6, QFormLayout.FieldRole, self.computerSelect)


        self.horizontalLayout_11.addLayout(self.formLayout_6)

        self.verticalLayout_11 = QVBoxLayout()
        self.verticalLayout_11.setObjectName("verticalLayout_11")
        self.verticalLayout_10 = QVBoxLayout()
        self.verticalLayout_10.setObjectName("verticalLayout_10")
        self.skippableCheckbox = QCheckBox(self.fileTab)
        self.skippableCheckbox.setObjectName("skippableCheckbox")

        self.verticalLayout_10.addWidget(self.skippableCheckbox)

        self.animatedCutCheckbox = QCheckBox(self.fileTab)
        self.animatedCutCheckbox.setObjectName("animatedCutCheckbox")

        self.verticalLayout_10.addWidget(self.animatedCutCheckbox)

        self.oldHitCheckbox = QCheckBox(self.fileTab)
        self.oldHitCheckbox.setObjectName("oldHitCheckbox")

        self.verticalLayout_10.addWidget(self.oldHitCheckbox)

        self.unequipHandsCheckbox = QCheckBox(self.fileTab)
        self.unequipHandsCheckbox.setObjectName("unequipHandsCheckbox")

        self.verticalLayout_10.addWidget(self.unequipHandsCheckbox)

        self.unequipAllCheckbox = QCheckBox(self.fileTab)
        self.unequipAllCheckbox.setObjectName("unequipAllCheckbox")

        self.verticalLayout_10.addWidget(self.unequipAllCheckbox)


        self.verticalLayout_11.addLayout(self.verticalLayout_10)

        self.formLayout_7 = QFormLayout()
        self.formLayout_7.setObjectName("formLayout_7")
        self.label_44 = QLabel(self.fileTab)
        self.label_44.setObjectName("label_44")

        self.formLayout_7.setWidget(0, QFormLayout.LabelRole, self.label_44)

        self.entryDelaySpin = GFFFieldSpinBox(self.fileTab)
        self.entryDelaySpin.setObjectName("entryDelaySpin")
        self.entryDelaySpin.setMinimum(-2147483648)
        self.entryDelaySpin.setMaximum(2147483647)

        self.formLayout_7.setWidget(0, QFormLayout.FieldRole, self.entryDelaySpin)

        self.label_45 = QLabel(self.fileTab)
        self.label_45.setObjectName("label_45")

        self.formLayout_7.setWidget(1, QFormLayout.LabelRole, self.label_45)

        self.replyDelaySpin = GFFFieldSpinBox(self.fileTab)
        self.replyDelaySpin.setObjectName("replyDelaySpin")
        self.replyDelaySpin.setMinimum(-2147483648)
        self.replyDelaySpin.setMaximum(2147483647)

        self.formLayout_7.setWidget(1, QFormLayout.FieldRole, self.replyDelaySpin)


        self.verticalLayout_11.addLayout(self.formLayout_7)


        self.horizontalLayout_11.addLayout(self.verticalLayout_11)

        self.verticalLayout_12 = QVBoxLayout()
        self.verticalLayout_12.setObjectName("verticalLayout_12")
        self.label_46 = QLabel(self.fileTab)
        self.label_46.setObjectName("label_46")

        self.verticalLayout_12.addWidget(self.label_46)

        self.stuntList = QListWidget(self.fileTab)
        self.stuntList.setObjectName("stuntList")

        self.verticalLayout_12.addWidget(self.stuntList)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        self.addStuntButton = QPushButton(self.fileTab)
        self.addStuntButton.setObjectName("addStuntButton")

        self.horizontalLayout_13.addWidget(self.addStuntButton)

        self.removeStuntButton = QPushButton(self.fileTab)
        self.removeStuntButton.setObjectName("removeStuntButton")

        self.horizontalLayout_13.addWidget(self.removeStuntButton)

        self.editStuntButton = QPushButton(self.fileTab)
        self.editStuntButton.setObjectName("editStuntButton")

        self.horizontalLayout_13.addWidget(self.editStuntButton)


        self.verticalLayout_12.addLayout(self.horizontalLayout_13)


        self.horizontalLayout_11.addLayout(self.verticalLayout_12)

        self.tabWidget.addTab(self.fileTab, "")
        self.scriptsTab = QWidget()
        self.scriptsTab.setObjectName("scriptsTab")
        self.verticalLayout_3 = QVBoxLayout(self.scriptsTab)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.label_16 = QLabel(self.scriptsTab)
        self.label_16.setObjectName("label_16")
        self.label_16.setMinimumSize(QSize(80, 0))

        self.horizontalLayout_6.addWidget(self.label_16)

        self.label_5 = QLabel(self.scriptsTab)
        self.label_5.setObjectName("label_5")

        self.horizontalLayout_6.addWidget(self.label_5)

        self.label_6 = QLabel(self.scriptsTab)
        self.label_6.setObjectName("label_6")
        self.label_6.setMinimumSize(QSize(85, 0))

        self.horizontalLayout_6.addWidget(self.label_6)

        self.label_7 = QLabel(self.scriptsTab)
        self.label_7.setObjectName("label_7")
        self.label_7.setMinimumSize(QSize(85, 0))

        self.horizontalLayout_6.addWidget(self.label_7)

        self.label_8 = QLabel(self.scriptsTab)
        self.label_8.setObjectName("label_8")
        self.label_8.setMinimumSize(QSize(85, 0))

        self.horizontalLayout_6.addWidget(self.label_8)

        self.label_9 = QLabel(self.scriptsTab)
        self.label_9.setObjectName("label_9")
        self.label_9.setMinimumSize(QSize(85, 0))

        self.horizontalLayout_6.addWidget(self.label_9)

        self.label_10 = QLabel(self.scriptsTab)
        self.label_10.setObjectName("label_10")
        self.label_10.setMinimumSize(QSize(85, 0))

        self.horizontalLayout_6.addWidget(self.label_10)

        self.label_11 = QLabel(self.scriptsTab)
        self.label_11.setObjectName("label_11")

        self.horizontalLayout_6.addWidget(self.label_11)

        self.horizontalSpacer_6 = QSpacerItem(19, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_6)

        self.horizontalLayout_6.setStretch(1, 3)
        self.horizontalLayout_6.setStretch(2, 1)
        self.horizontalLayout_6.setStretch(3, 1)
        self.horizontalLayout_6.setStretch(4, 1)
        self.horizontalLayout_6.setStretch(5, 1)
        self.horizontalLayout_6.setStretch(6, 1)
        self.horizontalLayout_6.setStretch(7, 2)

        self.verticalLayout_3.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.script1Label = QLabel(self.scriptsTab)
        self.script1Label.setObjectName("script1Label")
        self.script1Label.setMinimumSize(QSize(80, 0))

        self.horizontalLayout_2.addWidget(self.script1Label)

        self.script1ResrefEdit = FilterComboBox(self.scriptsTab)
        self.script1ResrefEdit.setObjectName("script1ResrefEdit")

        self.horizontalLayout_2.addWidget(self.script1ResrefEdit)

        self.script1Param1Spin = GFFFieldSpinBox(self.scriptsTab)
        self.script1Param1Spin.setObjectName("script1Param1Spin")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.script1Param1Spin.sizePolicy().hasHeightForWidth())
        self.script1Param1Spin.setSizePolicy(sizePolicy)
        self.script1Param1Spin.setMinimum(-2147483647)
        self.script1Param1Spin.setMaximum(2147483647)

        self.horizontalLayout_2.addWidget(self.script1Param1Spin)

        self.script1Param2Spin = GFFFieldSpinBox(self.scriptsTab)
        self.script1Param2Spin.setObjectName("script1Param2Spin")
        sizePolicy.setHeightForWidth(self.script1Param2Spin.sizePolicy().hasHeightForWidth())
        self.script1Param2Spin.setSizePolicy(sizePolicy)
        self.script1Param2Spin.setMinimum(-2147483647)
        self.script1Param2Spin.setMaximum(2147483647)

        self.horizontalLayout_2.addWidget(self.script1Param2Spin)

        self.script1Param3Spin = GFFFieldSpinBox(self.scriptsTab)
        self.script1Param3Spin.setObjectName("script1Param3Spin")
        sizePolicy.setHeightForWidth(self.script1Param3Spin.sizePolicy().hasHeightForWidth())
        self.script1Param3Spin.setSizePolicy(sizePolicy)
        self.script1Param3Spin.setMinimum(-2147483647)
        self.script1Param3Spin.setMaximum(2147483647)

        self.horizontalLayout_2.addWidget(self.script1Param3Spin)

        self.script1Param4Spin = GFFFieldSpinBox(self.scriptsTab)
        self.script1Param4Spin.setObjectName("script1Param4Spin")
        sizePolicy.setHeightForWidth(self.script1Param4Spin.sizePolicy().hasHeightForWidth())
        self.script1Param4Spin.setSizePolicy(sizePolicy)
        self.script1Param4Spin.setMinimum(-2147483647)
        self.script1Param4Spin.setMaximum(2147483647)

        self.horizontalLayout_2.addWidget(self.script1Param4Spin)

        self.script1Param5Spin = GFFFieldSpinBox(self.scriptsTab)
        self.script1Param5Spin.setObjectName("script1Param5Spin")
        sizePolicy.setHeightForWidth(self.script1Param5Spin.sizePolicy().hasHeightForWidth())
        self.script1Param5Spin.setSizePolicy(sizePolicy)
        self.script1Param5Spin.setMinimum(-2147483647)
        self.script1Param5Spin.setMaximum(2147483647)

        self.horizontalLayout_2.addWidget(self.script1Param5Spin)

        self.script1Param6Edit = QLineEdit(self.scriptsTab)
        self.script1Param6Edit.setObjectName("script1Param6Edit")

        self.horizontalLayout_2.addWidget(self.script1Param6Edit)

        self.horizontalSpacer_4 = QSpacerItem(19, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_4)

        self.horizontalLayout_2.setStretch(1, 3)
        self.horizontalLayout_2.setStretch(2, 1)
        self.horizontalLayout_2.setStretch(3, 1)
        self.horizontalLayout_2.setStretch(4, 1)
        self.horizontalLayout_2.setStretch(5, 1)
        self.horizontalLayout_2.setStretch(6, 1)
        self.horizontalLayout_2.setStretch(7, 2)

        self.verticalLayout_3.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.script2Label = QLabel(self.scriptsTab)
        self.script2Label.setObjectName("script2Label")
        self.script2Label.setMinimumSize(QSize(80, 0))

        self.horizontalLayout_3.addWidget(self.script2Label)

        self.script2ResrefEdit = FilterComboBox(self.scriptsTab)
        self.script2ResrefEdit.setObjectName("script2ResrefEdit")

        self.horizontalLayout_3.addWidget(self.script2ResrefEdit)

        self.script2Param1Spin = GFFFieldSpinBox(self.scriptsTab)
        self.script2Param1Spin.setObjectName("script2Param1Spin")
        sizePolicy.setHeightForWidth(self.script2Param1Spin.sizePolicy().hasHeightForWidth())
        self.script2Param1Spin.setSizePolicy(sizePolicy)
        self.script2Param1Spin.setMinimum(-2147483647)
        self.script2Param1Spin.setMaximum(2147483647)

        self.horizontalLayout_3.addWidget(self.script2Param1Spin)

        self.script2Param2Spin = GFFFieldSpinBox(self.scriptsTab)
        self.script2Param2Spin.setObjectName("script2Param2Spin")
        sizePolicy.setHeightForWidth(self.script2Param2Spin.sizePolicy().hasHeightForWidth())
        self.script2Param2Spin.setSizePolicy(sizePolicy)
        self.script2Param2Spin.setMinimum(-2147483647)
        self.script2Param2Spin.setMaximum(2147483647)

        self.horizontalLayout_3.addWidget(self.script2Param2Spin)

        self.script2Param3Spin = GFFFieldSpinBox(self.scriptsTab)
        self.script2Param3Spin.setObjectName("script2Param3Spin")
        sizePolicy.setHeightForWidth(self.script2Param3Spin.sizePolicy().hasHeightForWidth())
        self.script2Param3Spin.setSizePolicy(sizePolicy)
        self.script2Param3Spin.setMinimum(-2147483647)
        self.script2Param3Spin.setMaximum(2147483647)

        self.horizontalLayout_3.addWidget(self.script2Param3Spin)

        self.script2Param4Spin = GFFFieldSpinBox(self.scriptsTab)
        self.script2Param4Spin.setObjectName("script2Param4Spin")
        sizePolicy.setHeightForWidth(self.script2Param4Spin.sizePolicy().hasHeightForWidth())
        self.script2Param4Spin.setSizePolicy(sizePolicy)
        self.script2Param4Spin.setMinimum(-2147483647)
        self.script2Param4Spin.setMaximum(2147483647)

        self.horizontalLayout_3.addWidget(self.script2Param4Spin)

        self.script2Param5Spin = GFFFieldSpinBox(self.scriptsTab)
        self.script2Param5Spin.setObjectName("script2Param5Spin")
        sizePolicy.setHeightForWidth(self.script2Param5Spin.sizePolicy().hasHeightForWidth())
        self.script2Param5Spin.setSizePolicy(sizePolicy)
        self.script2Param5Spin.setMinimum(-2147483647)
        self.script2Param5Spin.setMaximum(2147483647)

        self.horizontalLayout_3.addWidget(self.script2Param5Spin)

        self.script2Param6Edit = QLineEdit(self.scriptsTab)
        self.script2Param6Edit.setObjectName("script2Param6Edit")

        self.horizontalLayout_3.addWidget(self.script2Param6Edit)

        self.horizontalSpacer_5 = QSpacerItem(19, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_5)

        self.horizontalLayout_3.setStretch(1, 3)
        self.horizontalLayout_3.setStretch(2, 1)
        self.horizontalLayout_3.setStretch(3, 1)
        self.horizontalLayout_3.setStretch(4, 1)
        self.horizontalLayout_3.setStretch(5, 1)
        self.horizontalLayout_3.setStretch(6, 1)
        self.horizontalLayout_3.setStretch(7, 2)

        self.verticalLayout_3.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.conditional1Label = QLabel(self.scriptsTab)
        self.conditional1Label.setObjectName("conditional1Label")
        self.conditional1Label.setMinimumSize(QSize(80, 0))

        self.horizontalLayout_4.addWidget(self.conditional1Label)

        self.condition1ResrefEdit = FilterComboBox(self.scriptsTab)
        self.condition1ResrefEdit.setObjectName("condition1ResrefEdit")

        self.horizontalLayout_4.addWidget(self.condition1ResrefEdit)

        self.condition1Param1Spin = GFFFieldSpinBox(self.scriptsTab)
        self.condition1Param1Spin.setObjectName("condition1Param1Spin")
        sizePolicy.setHeightForWidth(self.condition1Param1Spin.sizePolicy().hasHeightForWidth())
        self.condition1Param1Spin.setSizePolicy(sizePolicy)
        self.condition1Param1Spin.setMinimum(-2147483647)
        self.condition1Param1Spin.setMaximum(2147483647)

        self.horizontalLayout_4.addWidget(self.condition1Param1Spin)

        self.condition1Param2Spin = GFFFieldSpinBox(self.scriptsTab)
        self.condition1Param2Spin.setObjectName("condition1Param2Spin")
        sizePolicy.setHeightForWidth(self.condition1Param2Spin.sizePolicy().hasHeightForWidth())
        self.condition1Param2Spin.setSizePolicy(sizePolicy)
        self.condition1Param2Spin.setMinimum(-2147483647)
        self.condition1Param2Spin.setMaximum(2147483647)

        self.horizontalLayout_4.addWidget(self.condition1Param2Spin)

        self.condition1Param3Spin = GFFFieldSpinBox(self.scriptsTab)
        self.condition1Param3Spin.setObjectName("condition1Param3Spin")
        sizePolicy.setHeightForWidth(self.condition1Param3Spin.sizePolicy().hasHeightForWidth())
        self.condition1Param3Spin.setSizePolicy(sizePolicy)
        self.condition1Param3Spin.setMinimum(-2147483647)
        self.condition1Param3Spin.setMaximum(2147483647)

        self.horizontalLayout_4.addWidget(self.condition1Param3Spin)

        self.condition1Param4Spin = GFFFieldSpinBox(self.scriptsTab)
        self.condition1Param4Spin.setObjectName("condition1Param4Spin")
        sizePolicy.setHeightForWidth(self.condition1Param4Spin.sizePolicy().hasHeightForWidth())
        self.condition1Param4Spin.setSizePolicy(sizePolicy)
        self.condition1Param4Spin.setMinimum(-2147483647)
        self.condition1Param4Spin.setMaximum(2147483647)

        self.horizontalLayout_4.addWidget(self.condition1Param4Spin)

        self.condition1Param5Spin = GFFFieldSpinBox(self.scriptsTab)
        self.condition1Param5Spin.setObjectName("condition1Param5Spin")
        sizePolicy.setHeightForWidth(self.condition1Param5Spin.sizePolicy().hasHeightForWidth())
        self.condition1Param5Spin.setSizePolicy(sizePolicy)
        self.condition1Param5Spin.setMinimum(-2147483647)
        self.condition1Param5Spin.setMaximum(2147483647)

        self.horizontalLayout_4.addWidget(self.condition1Param5Spin)

        self.condition1Param6Edit = QLineEdit(self.scriptsTab)
        self.condition1Param6Edit.setObjectName("condition1Param6Edit")

        self.horizontalLayout_4.addWidget(self.condition1Param6Edit)

        self.condition1NotCheckbox = QCheckBox(self.scriptsTab)
        self.condition1NotCheckbox.setObjectName("condition1NotCheckbox")

        self.horizontalLayout_4.addWidget(self.condition1NotCheckbox)

        self.horizontalLayout_4.setStretch(1, 3)
        self.horizontalLayout_4.setStretch(2, 1)
        self.horizontalLayout_4.setStretch(3, 1)
        self.horizontalLayout_4.setStretch(4, 1)
        self.horizontalLayout_4.setStretch(5, 1)
        self.horizontalLayout_4.setStretch(6, 1)
        self.horizontalLayout_4.setStretch(7, 2)

        self.verticalLayout_3.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.conditional2Label = QLabel(self.scriptsTab)
        self.conditional2Label.setObjectName("conditional2Label")
        self.conditional2Label.setMinimumSize(QSize(80, 0))

        self.horizontalLayout_5.addWidget(self.conditional2Label)

        self.condition2ResrefEdit = FilterComboBox(self.scriptsTab)
        self.condition2ResrefEdit.setObjectName("condition2ResrefEdit")

        self.horizontalLayout_5.addWidget(self.condition2ResrefEdit)

        self.condition2Param1Spin = GFFFieldSpinBox(self.scriptsTab)
        self.condition2Param1Spin.setObjectName("condition2Param1Spin")
        sizePolicy.setHeightForWidth(self.condition2Param1Spin.sizePolicy().hasHeightForWidth())
        self.condition2Param1Spin.setSizePolicy(sizePolicy)
        self.condition2Param1Spin.setMinimum(-2147483647)
        self.condition2Param1Spin.setMaximum(2147483647)

        self.horizontalLayout_5.addWidget(self.condition2Param1Spin)

        self.condition2Param2Spin = GFFFieldSpinBox(self.scriptsTab)
        self.condition2Param2Spin.setObjectName("condition2Param2Spin")
        sizePolicy.setHeightForWidth(self.condition2Param2Spin.sizePolicy().hasHeightForWidth())
        self.condition2Param2Spin.setSizePolicy(sizePolicy)
        self.condition2Param2Spin.setMinimum(-2147483647)
        self.condition2Param2Spin.setMaximum(2147483647)

        self.horizontalLayout_5.addWidget(self.condition2Param2Spin)

        self.condition2Param3Spin = GFFFieldSpinBox(self.scriptsTab)
        self.condition2Param3Spin.setObjectName("condition2Param3Spin")
        sizePolicy.setHeightForWidth(self.condition2Param3Spin.sizePolicy().hasHeightForWidth())
        self.condition2Param3Spin.setSizePolicy(sizePolicy)
        self.condition2Param3Spin.setMinimum(-2147483647)
        self.condition2Param3Spin.setMaximum(2147483647)

        self.horizontalLayout_5.addWidget(self.condition2Param3Spin)

        self.condition2Param4Spin = GFFFieldSpinBox(self.scriptsTab)
        self.condition2Param4Spin.setObjectName("condition2Param4Spin")
        sizePolicy.setHeightForWidth(self.condition2Param4Spin.sizePolicy().hasHeightForWidth())
        self.condition2Param4Spin.setSizePolicy(sizePolicy)
        self.condition2Param4Spin.setMinimum(-2147483647)
        self.condition2Param4Spin.setMaximum(2147483647)

        self.horizontalLayout_5.addWidget(self.condition2Param4Spin)

        self.condition2Param5Spin = GFFFieldSpinBox(self.scriptsTab)
        self.condition2Param5Spin.setObjectName("condition2Param5Spin")
        sizePolicy.setHeightForWidth(self.condition2Param5Spin.sizePolicy().hasHeightForWidth())
        self.condition2Param5Spin.setSizePolicy(sizePolicy)
        self.condition2Param5Spin.setMinimum(-2147483647)
        self.condition2Param5Spin.setMaximum(2147483647)

        self.horizontalLayout_5.addWidget(self.condition2Param5Spin)

        self.condition2Param6Edit = QLineEdit(self.scriptsTab)
        self.condition2Param6Edit.setObjectName("condition2Param6Edit")

        self.horizontalLayout_5.addWidget(self.condition2Param6Edit)

        self.condition2NotCheckbox = QCheckBox(self.scriptsTab)
        self.condition2NotCheckbox.setObjectName("condition2NotCheckbox")

        self.horizontalLayout_5.addWidget(self.condition2NotCheckbox)

        self.horizontalLayout_5.setStretch(1, 3)
        self.horizontalLayout_5.setStretch(2, 1)
        self.horizontalLayout_5.setStretch(3, 1)
        self.horizontalLayout_5.setStretch(4, 1)
        self.horizontalLayout_5.setStretch(5, 1)
        self.horizontalLayout_5.setStretch(6, 1)
        self.horizontalLayout_5.setStretch(7, 2)

        self.verticalLayout_3.addLayout(self.horizontalLayout_5)

        self.verticalSpacer = QSpacerItem(20, 95, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.tabWidget.addTab(self.scriptsTab, "")
        self.animsTab = QWidget()
        self.animsTab.setObjectName("animsTab")
        self.horizontalLayout_12 = QHBoxLayout(self.animsTab)
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.label_12 = QLabel(self.animsTab)
        self.label_12.setObjectName("label_12")

        self.verticalLayout_5.addWidget(self.label_12)

        self.animsList = QListWidget(self.animsTab)
        self.animsList.setObjectName("animsList")

        self.verticalLayout_5.addWidget(self.animsList)


        self.horizontalLayout_7.addLayout(self.verticalLayout_5)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.addAnimButton = QPushButton(self.animsTab)
        self.addAnimButton.setObjectName("addAnimButton")

        self.verticalLayout_4.addWidget(self.addAnimButton)

        self.removeAnimButton = QPushButton(self.animsTab)
        self.removeAnimButton.setObjectName("removeAnimButton")

        self.verticalLayout_4.addWidget(self.removeAnimButton)

        self.editAnimButton = QPushButton(self.animsTab)
        self.editAnimButton.setObjectName("editAnimButton")

        self.verticalLayout_4.addWidget(self.editAnimButton)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_3)


        self.horizontalLayout_7.addLayout(self.verticalLayout_4)


        self.horizontalLayout_12.addLayout(self.horizontalLayout_7)

        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label_17 = QLabel(self.animsTab)
        self.label_17.setObjectName("label_17")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_17)

        self.emotionSelect = ComboBox2DA(self.animsTab)
        self.emotionSelect.setObjectName("emotionSelect")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.emotionSelect)

        self.label_18 = QLabel(self.animsTab)
        self.label_18.setObjectName("label_18")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_18)

        self.expressionSelect = ComboBox2DA(self.animsTab)
        self.expressionSelect.setObjectName("expressionSelect")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.expressionSelect)


        self.verticalLayout_7.addLayout(self.formLayout)

        self.line = QFrame(self.animsTab)
        self.line.setObjectName("line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_7.addWidget(self.line)

        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName("formLayout_2")
        self.label_19 = QLabel(self.animsTab)
        self.label_19.setObjectName("label_19")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_19)

        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.soundComboBox = FilterComboBox(self.animsTab)
        self.soundComboBox.setObjectName("soundComboBox")

        self.verticalLayout_6.addWidget(self.soundComboBox)

        self.soundButton = QPushButton(self.animsTab)
        self.soundButton.setObjectName("soundButton")

        self.verticalLayout_6.addWidget(self.soundButton)


        self.formLayout_2.setLayout(0, QFormLayout.FieldRole, self.verticalLayout_6)

        self.label_20 = QLabel(self.animsTab)
        self.label_20.setObjectName("label_20")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_20)

        self.verticalLayout_8 = QVBoxLayout()
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.voiceComboBox = FilterComboBox(self.animsTab)
        self.voiceComboBox.setObjectName("voiceComboBox")

        self.verticalLayout_8.addWidget(self.voiceComboBox)

        self.voiceButton = QPushButton(self.animsTab)
        self.voiceButton.setObjectName("voiceButton")

        self.verticalLayout_8.addWidget(self.voiceButton)


        self.formLayout_2.setLayout(1, QFormLayout.FieldRole, self.verticalLayout_8)

        self.soundCheckbox = QCheckBox(self.animsTab)
        self.soundCheckbox.setObjectName("soundCheckbox")

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.soundCheckbox)


        self.verticalLayout_7.addLayout(self.formLayout_2)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_7.addItem(self.verticalSpacer_2)


        self.horizontalLayout_12.addLayout(self.verticalLayout_7)

        self.tabWidget.addTab(self.animsTab, "")
        self.journalTab = QWidget()
        self.journalTab.setObjectName("journalTab")
        self.horizontalLayout_8 = QHBoxLayout(self.journalTab)
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.formLayout_3 = QFormLayout()
        self.formLayout_3.setObjectName("formLayout_3")
        self.label_22 = QLabel(self.journalTab)
        self.label_22.setObjectName("label_22")

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label_22)

        self.plotIndexSpin = GFFFieldSpinBox(self.journalTab)
        self.plotIndexSpin.setObjectName("plotIndexSpin")
        self.plotIndexSpin.setMinimum(-1)
        self.plotIndexSpin.setMaximum(10000)

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.plotIndexSpin)

        self.label_23 = QLabel(self.journalTab)
        self.label_23.setObjectName("label_23")

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.label_23)

        self.label_24 = QLabel(self.journalTab)
        self.label_24.setObjectName("label_24")

        self.formLayout_3.setWidget(2, QFormLayout.LabelRole, self.label_24)

        self.label_25 = QLabel(self.journalTab)
        self.label_25.setObjectName("label_25")

        self.formLayout_3.setWidget(3, QFormLayout.LabelRole, self.label_25)

        self.questEntrySpin = GFFFieldSpinBox(self.journalTab)
        self.questEntrySpin.setObjectName("questEntrySpin")
        self.questEntrySpin.setMinimum(-2147483648)
        self.questEntrySpin.setMaximum(2147483647)

        self.formLayout_3.setWidget(3, QFormLayout.FieldRole, self.questEntrySpin)

        self.plotXpSpin = QDoubleSpinBox(self.journalTab)
        self.plotXpSpin.setObjectName("plotXpSpin")

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.plotXpSpin)

        self.questEdit = QLineEdit(self.journalTab)
        self.questEdit.setObjectName("questEdit")

        self.formLayout_3.setWidget(2, QFormLayout.FieldRole, self.questEdit)


        self.horizontalLayout_8.addLayout(self.formLayout_3)

        self.horizontalSpacer = QSpacerItem(516, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer)

        self.horizontalLayout_8.setStretch(0, 1)
        self.horizontalLayout_8.setStretch(1, 2)
        self.tabWidget.addTab(self.journalTab, "")
        self.cameraTab = QWidget()
        self.cameraTab.setObjectName("cameraTab")
        self.horizontalLayout_9 = QHBoxLayout(self.cameraTab)
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.formLayout_4 = QFormLayout()
        self.formLayout_4.setObjectName("formLayout_4")
        self.label_26 = QLabel(self.cameraTab)
        self.label_26.setObjectName("label_26")

        self.formLayout_4.setWidget(0, QFormLayout.LabelRole, self.label_26)

        self.cameraIdSpin = GFFFieldSpinBox(self.cameraTab)
        self.cameraIdSpin.setObjectName("cameraIdSpin")
        self.cameraIdSpin.setMinimum(-1)
        self.cameraIdSpin.setMaximum(10000)

        self.formLayout_4.setWidget(0, QFormLayout.FieldRole, self.cameraIdSpin)

        self.label_27 = QLabel(self.cameraTab)
        self.label_27.setObjectName("label_27")

        self.formLayout_4.setWidget(1, QFormLayout.LabelRole, self.label_27)

        self.label_28 = QLabel(self.cameraTab)
        self.label_28.setObjectName("label_28")

        self.formLayout_4.setWidget(2, QFormLayout.LabelRole, self.label_28)

        self.cameraAnimSpin = GFFFieldSpinBox(self.cameraTab)
        self.cameraAnimSpin.setObjectName("cameraAnimSpin")
        self.cameraAnimSpin.setMinimum(-1)
        self.cameraAnimSpin.setMaximum(65534)

        self.formLayout_4.setWidget(1, QFormLayout.FieldRole, self.cameraAnimSpin)

        self.label_29 = QLabel(self.cameraTab)
        self.label_29.setObjectName("label_29")

        self.formLayout_4.setWidget(3, QFormLayout.LabelRole, self.label_29)

        self.cameraEffectSelect = QComboBox(self.cameraTab)
        self.cameraEffectSelect.setObjectName("cameraEffectSelect")

        self.formLayout_4.setWidget(3, QFormLayout.FieldRole, self.cameraEffectSelect)

        self.cameraAngleSelect = QComboBox(self.cameraTab)
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.setObjectName("cameraAngleSelect")

        self.formLayout_4.setWidget(2, QFormLayout.FieldRole, self.cameraAngleSelect)


        self.horizontalLayout_9.addLayout(self.formLayout_4)

        self.horizontalSpacer_2 = QSpacerItem(324, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_2)

        self.horizontalLayout_9.setStretch(0, 1)
        self.horizontalLayout_9.setStretch(1, 1)
        self.tabWidget.addTab(self.cameraTab, "")
        self.otherTab = QWidget()
        self.otherTab.setObjectName("otherTab")
        self.horizontalLayout_10 = QHBoxLayout(self.otherTab)
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.verticalLayout_9 = QVBoxLayout()
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.nodeUnskippableCheckbox = QCheckBox(self.otherTab)
        self.nodeUnskippableCheckbox.setObjectName("nodeUnskippableCheckbox")

        self.verticalLayout_9.addWidget(self.nodeUnskippableCheckbox)

        self.formLayout_5 = QFormLayout()
        self.formLayout_5.setObjectName("formLayout_5")
        self.label_30 = QLabel(self.otherTab)
        self.label_30.setObjectName("label_30")

        self.formLayout_5.setWidget(0, QFormLayout.LabelRole, self.label_30)

        self.nodeIdSpin = GFFFieldSpinBox(self.otherTab)
        self.nodeIdSpin.setObjectName("nodeIdSpin")
        self.nodeIdSpin.setMaximum(999999)

        self.formLayout_5.setWidget(0, QFormLayout.FieldRole, self.nodeIdSpin)

        self.label_31 = QLabel(self.otherTab)
        self.label_31.setObjectName("label_31")

        self.formLayout_5.setWidget(1, QFormLayout.LabelRole, self.label_31)

        self.alienRaceNodeSpin = GFFFieldSpinBox(self.otherTab)
        self.alienRaceNodeSpin.setObjectName("alienRaceNodeSpin")
        self.alienRaceNodeSpin.setMinimum(-1)
        self.alienRaceNodeSpin.setMaximum(2147483647)

        self.formLayout_5.setWidget(1, QFormLayout.FieldRole, self.alienRaceNodeSpin)

        self.label_32 = QLabel(self.otherTab)
        self.label_32.setObjectName("label_32")

        self.formLayout_5.setWidget(2, QFormLayout.LabelRole, self.label_32)

        self.postProcSpin = GFFFieldSpinBox(self.otherTab)
        self.postProcSpin.setObjectName("postProcSpin")
        self.postProcSpin.setMinimum(-1)
        self.postProcSpin.setMaximum(2147483647)

        self.formLayout_5.setWidget(2, QFormLayout.FieldRole, self.postProcSpin)

        self.label_33 = QLabel(self.otherTab)
        self.label_33.setObjectName("label_33")

        self.formLayout_5.setWidget(3, QFormLayout.LabelRole, self.label_33)

        self.delaySpin = GFFFieldSpinBox(self.otherTab)
        self.delaySpin.setObjectName("delaySpin")
        self.delaySpin.setMinimum(-1)
        self.delaySpin.setMaximum(2147483647)

        self.formLayout_5.setWidget(3, QFormLayout.FieldRole, self.delaySpin)

        self.label_34 = QLabel(self.otherTab)
        self.label_34.setObjectName("label_34")

        self.formLayout_5.setWidget(4, QFormLayout.LabelRole, self.label_34)

        self.logicSpin = GFFFieldSpinBox(self.otherTab)
        self.logicSpin.setObjectName("logicSpin")
        self.logicSpin.setMinimum(-1)
        self.logicSpin.setMaximum(2147483647)

        self.formLayout_5.setWidget(4, QFormLayout.FieldRole, self.logicSpin)

        self.label_35 = QLabel(self.otherTab)
        self.label_35.setObjectName("label_35")

        self.formLayout_5.setWidget(5, QFormLayout.LabelRole, self.label_35)

        self.waitFlagSpin = GFFFieldSpinBox(self.otherTab)
        self.waitFlagSpin.setObjectName("waitFlagSpin")
        self.waitFlagSpin.setMinimum(-1)
        self.waitFlagSpin.setMaximum(2147483647)

        self.formLayout_5.setWidget(5, QFormLayout.FieldRole, self.waitFlagSpin)

        self.label_36 = QLabel(self.otherTab)
        self.label_36.setObjectName("label_36")

        self.formLayout_5.setWidget(6, QFormLayout.LabelRole, self.label_36)

        self.fadeTypeSpin = GFFFieldSpinBox(self.otherTab)
        self.fadeTypeSpin.setObjectName("fadeTypeSpin")
        self.fadeTypeSpin.setMinimum(-1)
        self.fadeTypeSpin.setMaximum(2147483647)

        self.formLayout_5.setWidget(6, QFormLayout.FieldRole, self.fadeTypeSpin)


        self.verticalLayout_9.addLayout(self.formLayout_5)


        self.horizontalLayout_10.addLayout(self.verticalLayout_9)

        self.horizontalSpacer_3 = QSpacerItem(324, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer_3)

        self.horizontalLayout_10.setStretch(0, 1)
        self.horizontalLayout_10.setStretch(1, 1)
        self.tabWidget.addTab(self.otherTab, "")
        self.commentsTab = QWidget()
        self.commentsTab.setObjectName("commentsTab")
        self.gridLayout = QGridLayout(self.commentsTab)
        self.gridLayout.setObjectName("gridLayout")
        self.commentsEdit = QPlainTextEdit(self.commentsTab)
        self.commentsEdit.setObjectName("commentsEdit")

        self.gridLayout.addWidget(self.commentsEdit, 0, 0, 1, 1)

        self.tabWidget.addTab(self.commentsTab, "")

        self.horizontalLayout.addWidget(self.tabWidget)

        self.horizontalLayout.setStretch(0, 3)
        self.splitter.addWidget(self.layoutWidget)

        self.gridLayout_2.addWidget(self.splitter, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 1135, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuTools = QMenu(self.menubar)
        self.menuTools.setObjectName("menuTools")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuTools.menuAction())
        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSaveAs)
        self.menuFile.addAction(self.actionRevert)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuTools.addAction(self.actionReloadTree)
        self.menuTools.addAction(self.actionUnfocus)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(4)


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
        self.actionReloadTree.setText(QCoreApplication.translate("MainWindow", "Reload Tree", None))
        self.actionUnfocus.setText(QCoreApplication.translate("MainWindow", "Unfocus Tree", None))
        self.label.setText(QCoreApplication.translate("MainWindow", "Speaker Tag:", None))
        self.label_21.setText(QCoreApplication.translate("MainWindow", "Listener Tag:", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", "Text:", None))
        self.label_37.setText(QCoreApplication.translate("MainWindow", "Conversation Ends Script:", None))
        self.label_38.setText(QCoreApplication.translate("MainWindow", "Conversation Aborts Script:", None))
        self.label_39.setText(QCoreApplication.translate("MainWindow", "Voiceover ID:", None))
        self.label_40.setText(QCoreApplication.translate("MainWindow", "Ambient Track:", None))
        self.label_41.setText(QCoreApplication.translate("MainWindow", "Camera Model:", None))
        self.label_42.setText(QCoreApplication.translate("MainWindow", "Conversation Type:", None))
        self.label_43.setText(QCoreApplication.translate("MainWindow", "Computer Type:", None))
        self.conversationSelect.setItemText(0, QCoreApplication.translate("MainWindow", "Human", None))
        self.conversationSelect.setItemText(1, QCoreApplication.translate("MainWindow", "Computer", None))
        self.conversationSelect.setItemText(2, QCoreApplication.translate("MainWindow", "Type 3", None))
        self.conversationSelect.setItemText(3, QCoreApplication.translate("MainWindow", "Type 4", None))
        self.conversationSelect.setItemText(4, QCoreApplication.translate("MainWindow", "Type 5", None))

        self.computerSelect.setItemText(0, QCoreApplication.translate("MainWindow", "Modern", None))
        self.computerSelect.setItemText(1, QCoreApplication.translate("MainWindow", "Ancient", None))

        self.skippableCheckbox.setText(QCoreApplication.translate("MainWindow", "Skippable", None))
        self.animatedCutCheckbox.setText(QCoreApplication.translate("MainWindow", "Animated Cut", None))
        self.oldHitCheckbox.setText(QCoreApplication.translate("MainWindow", "Old Hit Check", None))
        self.unequipHandsCheckbox.setText(QCoreApplication.translate("MainWindow", "Unequip Hands", None))
        self.unequipAllCheckbox.setText(QCoreApplication.translate("MainWindow", "Unequip All", None))
        self.label_44.setText(QCoreApplication.translate("MainWindow", "Delay before entry:", None))
        self.label_45.setText(QCoreApplication.translate("MainWindow", "Delay before reply:", None))
        self.label_46.setText(QCoreApplication.translate("MainWindow", "Cutscene Model:", None))
        self.addStuntButton.setText(QCoreApplication.translate("MainWindow", "Add", None))
        self.removeStuntButton.setText(QCoreApplication.translate("MainWindow", "Remove", None))
        self.editStuntButton.setText(QCoreApplication.translate("MainWindow", "Edit", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.fileTab), QCoreApplication.translate("MainWindow", "This File", None))
        self.label_16.setText("")
        self.label_5.setText(QCoreApplication.translate("MainWindow", "ResRef", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", "P1", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", "P2", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", "P3", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", "P4", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", "P5", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", "P6", None))
        self.script1Label.setText(QCoreApplication.translate("MainWindow", "Script #1:", None))
        self.script2Label.setText(QCoreApplication.translate("MainWindow", "Script #2:", None))
        self.conditional1Label.setText(QCoreApplication.translate("MainWindow", "Conditional #1:", None))
        self.condition1NotCheckbox.setText("")
        self.conditional2Label.setText(QCoreApplication.translate("MainWindow", "Conditional #2:", None))
        self.condition2NotCheckbox.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.scriptsTab), QCoreApplication.translate("MainWindow", "Scripts", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", "Current Animations", None))
        self.addAnimButton.setText(QCoreApplication.translate("MainWindow", "Add", None))
        self.removeAnimButton.setText(QCoreApplication.translate("MainWindow", "Remove", None))
        self.editAnimButton.setText(QCoreApplication.translate("MainWindow", "Edit", None))
        self.label_17.setText(QCoreApplication.translate("MainWindow", "Emotion:", None))
        self.label_18.setText(QCoreApplication.translate("MainWindow", "Expression:", None))
        self.label_19.setText(QCoreApplication.translate("MainWindow", "Sound:", None))
        self.soundButton.setText(QCoreApplication.translate("MainWindow", "Play", None))
        self.label_20.setText(QCoreApplication.translate("MainWindow", "Voice:", None))
        self.voiceButton.setText(QCoreApplication.translate("MainWindow", "Play", None))
        self.soundCheckbox.setText(QCoreApplication.translate("MainWindow", "Enabled", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.animsTab), QCoreApplication.translate("MainWindow", "Animations", None))
        self.label_22.setText(QCoreApplication.translate("MainWindow", "Plot Index:", None))
        self.label_23.setText(QCoreApplication.translate("MainWindow", "Plot XP Percentage:", None))
        self.label_24.setText(QCoreApplication.translate("MainWindow", "Quest:", None))
        self.label_25.setText(QCoreApplication.translate("MainWindow", "Quest Entry:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.journalTab), QCoreApplication.translate("MainWindow", "Journal", None))
        self.label_26.setText(QCoreApplication.translate("MainWindow", "Camera ID:", None))
        self.label_27.setText(QCoreApplication.translate("MainWindow", "Camera Animation:", None))
        self.label_28.setText(QCoreApplication.translate("MainWindow", "Camera Angle:", None))
        self.label_29.setText(QCoreApplication.translate("MainWindow", "Camera Video Effect:", None))
        self.cameraAngleSelect.setItemText(0, QCoreApplication.translate("MainWindow", "Auto", None))
        self.cameraAngleSelect.setItemText(1, QCoreApplication.translate("MainWindow", "Face", None))
        self.cameraAngleSelect.setItemText(2, QCoreApplication.translate("MainWindow", "Shoulder", None))
        self.cameraAngleSelect.setItemText(3, QCoreApplication.translate("MainWindow", "Wide Shot", None))
        self.cameraAngleSelect.setItemText(4, QCoreApplication.translate("MainWindow", "Animated Camera", None))
        self.cameraAngleSelect.setItemText(5, QCoreApplication.translate("MainWindow", "No Change", None))
        self.cameraAngleSelect.setItemText(6, QCoreApplication.translate("MainWindow", "Static Camera", None))

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.cameraTab), QCoreApplication.translate("MainWindow", "Camera", None))
        self.nodeUnskippableCheckbox.setText(QCoreApplication.translate("MainWindow", "Node Unskippable", None))
        self.label_30.setText(QCoreApplication.translate("MainWindow", "Node ID:", None))
        self.label_31.setText(QCoreApplication.translate("MainWindow", "Alien Race Node:", None))
        self.label_32.setText(QCoreApplication.translate("MainWindow", "Post Proc Node:", None))
        self.label_33.setText(QCoreApplication.translate("MainWindow", "Delay:", None))
        self.label_34.setText(QCoreApplication.translate("MainWindow", "Logic:", None))
        self.label_35.setText(QCoreApplication.translate("MainWindow", "Wait Flags:", None))
        self.label_36.setText(QCoreApplication.translate("MainWindow", "Fade Type:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.otherTab), QCoreApplication.translate("MainWindow", "Other", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.commentsTab), QCoreApplication.translate("MainWindow", "Comments", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", "File", None))
        self.menuTools.setTitle(QCoreApplication.translate("MainWindow", "Tools", None))
    # retranslateUi

