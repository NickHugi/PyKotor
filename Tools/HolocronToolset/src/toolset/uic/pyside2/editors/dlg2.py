# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dlg2.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from toolset.gui.editors.dlg import DLGTreeView
from toolset.gui.widgets.edit.combobox_2da import ComboBox2DA
from toolset.gui.common.widgets.combobox import FilterComboBox
from toolset.gui.editors.dlg import GFFFieldSpinBox


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(4095, 2235)
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
        self.actionReloadTree = QAction(MainWindow)
        self.actionReloadTree.setObjectName(u"actionReloadTree")
        self.actionUnfocus = QAction(MainWindow)
        self.actionUnfocus.setObjectName(u"actionUnfocus")
        self.actionUnfocus.setEnabled(False)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout_2 = QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.splitter = QSplitter(self.centralwidget)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.leftWidget = QWidget(self.splitter)
        self.leftWidget.setObjectName(u"leftWidget")
        self.verticalLayout = QVBoxLayout(self.leftWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.dialogTree = DLGTreeView(self.leftWidget)
        self.dialogTree.setObjectName(u"dialogTree")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dialogTree.sizePolicy().hasHeightForWidth())
        self.dialogTree.setSizePolicy(sizePolicy)
        self.dialogTree.setMinimumSize(QSize(150, 0))
        self.dialogTree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.dialogTree.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.dialogTree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.dialogTree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dialogTree.header().setVisible(False)

        self.verticalLayout.addWidget(self.dialogTree)

        self.label = QLabel(self.leftWidget)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.speakerEdit = QLineEdit(self.leftWidget)
        self.speakerEdit.setObjectName(u"speakerEdit")

        self.verticalLayout.addWidget(self.speakerEdit)

        self.label_21 = QLabel(self.leftWidget)
        self.label_21.setObjectName(u"label_21")

        self.verticalLayout.addWidget(self.label_21)

        self.listenerEdit = QLineEdit(self.leftWidget)
        self.listenerEdit.setObjectName(u"listenerEdit")

        self.verticalLayout.addWidget(self.listenerEdit)

        self.label_2 = QLabel(self.leftWidget)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout.addWidget(self.label_2)

        self.textEdit = QPlainTextEdit(self.leftWidget)
        self.textEdit.setObjectName(u"textEdit")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.textEdit.sizePolicy().hasHeightForWidth())
        self.textEdit.setSizePolicy(sizePolicy1)
        self.textEdit.setReadOnly(True)

        self.verticalLayout.addWidget(self.textEdit)

        self.splitter.addWidget(self.leftWidget)
        self.rightWidget = QStackedWidget(self.splitter)
        self.rightWidget.setObjectName(u"rightWidget")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.rightWidget.sizePolicy().hasHeightForWidth())
        self.rightWidget.setSizePolicy(sizePolicy2)
        self.rightWidget.setMinimumSize(QSize(250, 0))
        self.rightWidget.setMaximumSize(QSize(1500, 16777215))
        self.rightWidget.setFocusPolicy(Qt.WheelFocus)
        self.scrollArea = QScrollArea()
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents_2 = QWidget()
        self.scrollAreaWidgetContents_2.setObjectName(u"scrollAreaWidgetContents_2")
        self.scrollArea.setWidget(self.scrollAreaWidgetContents_2)
        self.rightWidgetPage1 = QWidget()
        self.rightWidgetPage1.setObjectName(u"rightWidgetPage1")
        self.gridLayout = QGridLayout(self.rightWidgetPage1)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_37 = QLabel(self.rightWidgetPage1)
        self.label_37.setObjectName(u"label_37")

        self.gridLayout.addWidget(self.label_37, 0, 0, 1, 2)

        self.onEndEdit = FilterComboBox(self.rightWidgetPage1)
        self.onEndEdit.setObjectName(u"onEndEdit")

        self.gridLayout.addWidget(self.onEndEdit, 0, 1, 1, 1)

        self.label_38 = QLabel(self.rightWidgetPage1)
        self.label_38.setObjectName(u"label_38")

        self.gridLayout.addWidget(self.label_38, 1, 0, 1, 2)

        self.onAbortEdit = FilterComboBox(self.rightWidgetPage1)
        self.onAbortEdit.setObjectName(u"onAbortEdit")

        self.gridLayout.addWidget(self.onAbortEdit, 1, 1, 1, 1)

        self.label_39 = QLabel(self.rightWidgetPage1)
        self.label_39.setObjectName(u"label_39")

        self.gridLayout.addWidget(self.label_39, 2, 0, 1, 1)

        self.voIdEdit = QLineEdit(self.rightWidgetPage1)
        self.voIdEdit.setObjectName(u"voIdEdit")
        self.voIdEdit.setMaxLength(16)

        self.gridLayout.addWidget(self.voIdEdit, 2, 1, 1, 1)

        self.label_42 = QLabel(self.rightWidgetPage1)
        self.label_42.setObjectName(u"label_42")

        self.gridLayout.addWidget(self.label_42, 3, 0, 1, 1)

        self.conversationSelect = QComboBox(self.rightWidgetPage1)
        self.conversationSelect.addItem("")
        self.conversationSelect.addItem("")
        self.conversationSelect.addItem("")
        self.conversationSelect.addItem("")
        self.conversationSelect.addItem("")
        self.conversationSelect.setObjectName(u"conversationSelect")

        self.gridLayout.addWidget(self.conversationSelect, 3, 1, 1, 1)

        self.label_43 = QLabel(self.rightWidgetPage1)
        self.label_43.setObjectName(u"label_43")

        self.gridLayout.addWidget(self.label_43, 4, 0, 1, 1)

        self.computerSelect = QComboBox(self.rightWidgetPage1)
        self.computerSelect.addItem("")
        self.computerSelect.addItem("")
        self.computerSelect.setObjectName(u"computerSelect")

        self.gridLayout.addWidget(self.computerSelect, 4, 1, 1, 1)

        self.label_41 = QLabel(self.rightWidgetPage1)
        self.label_41.setObjectName(u"label_41")

        self.gridLayout.addWidget(self.label_41, 5, 0, 1, 1)

        self.cameraModelEdit = QLineEdit(self.rightWidgetPage1)
        self.cameraModelEdit.setObjectName(u"cameraModelEdit")
        self.cameraModelEdit.setMaxLength(16)

        self.gridLayout.addWidget(self.cameraModelEdit, 5, 1, 1, 1)

        self.label_40 = QLabel(self.rightWidgetPage1)
        self.label_40.setObjectName(u"label_40")

        self.gridLayout.addWidget(self.label_40, 6, 0, 1, 1)

        self.ambientTrackEdit = QLineEdit(self.rightWidgetPage1)
        self.ambientTrackEdit.setObjectName(u"ambientTrackEdit")
        self.ambientTrackEdit.setMaxLength(16)

        self.gridLayout.addWidget(self.ambientTrackEdit, 6, 1, 1, 1)

        self.label_22 = QLabel(self.rightWidgetPage1)
        self.label_22.setObjectName(u"label_22")

        self.gridLayout.addWidget(self.label_22, 7, 0, 1, 2)

        self.plotIndexSpin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.plotIndexSpin.setObjectName(u"plotIndexSpin")
        sizePolicy3 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.plotIndexSpin.sizePolicy().hasHeightForWidth())
        self.plotIndexSpin.setSizePolicy(sizePolicy3)
        self.plotIndexSpin.setMinimum(-1)
        self.plotIndexSpin.setMaximum(10000)

        self.gridLayout.addWidget(self.plotIndexSpin, 7, 1, 1, 1)

        self.label_23 = QLabel(self.rightWidgetPage1)
        self.label_23.setObjectName(u"label_23")

        self.gridLayout.addWidget(self.label_23, 8, 0, 1, 1)

        self.plotXpSpin = QSpinBox(self.rightWidgetPage1)
        self.plotXpSpin.setObjectName(u"plotXpSpin")

        self.gridLayout.addWidget(self.plotXpSpin, 8, 1, 1, 1)

        self.label_24 = QLabel(self.rightWidgetPage1)
        self.label_24.setObjectName(u"label_24")

        self.gridLayout.addWidget(self.label_24, 9, 0, 1, 1)

        self.questEdit = QLineEdit(self.rightWidgetPage1)
        self.questEdit.setObjectName(u"questEdit")

        self.gridLayout.addWidget(self.questEdit, 9, 1, 1, 1)

        self.label_25 = QLabel(self.rightWidgetPage1)
        self.label_25.setObjectName(u"label_25")

        self.gridLayout.addWidget(self.label_25, 10, 0, 1, 1)

        self.questEntrySpin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.questEntrySpin.setObjectName(u"questEntrySpin")
        self.questEntrySpin.setMinimum(-2147483648)
        self.questEntrySpin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.questEntrySpin, 10, 1, 1, 1)

        self.label_26 = QLabel(self.rightWidgetPage1)
        self.label_26.setObjectName(u"label_26")

        self.gridLayout.addWidget(self.label_26, 11, 0, 1, 1)

        self.cameraIdSpin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.cameraIdSpin.setObjectName(u"cameraIdSpin")
        self.cameraIdSpin.setMinimum(-1)
        self.cameraIdSpin.setMaximum(10000)

        self.gridLayout.addWidget(self.cameraIdSpin, 11, 1, 1, 1)

        self.label_27 = QLabel(self.rightWidgetPage1)
        self.label_27.setObjectName(u"label_27")

        self.gridLayout.addWidget(self.label_27, 12, 0, 1, 1)

        self.cameraAnimSpin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.cameraAnimSpin.setObjectName(u"cameraAnimSpin")
        self.cameraAnimSpin.setMinimum(-1)
        self.cameraAnimSpin.setMaximum(65534)

        self.gridLayout.addWidget(self.cameraAnimSpin, 12, 1, 1, 1)

        self.label_28 = QLabel(self.rightWidgetPage1)
        self.label_28.setObjectName(u"label_28")

        self.gridLayout.addWidget(self.label_28, 13, 0, 1, 1)

        self.cameraAngleSelect = QComboBox(self.rightWidgetPage1)
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.setObjectName(u"cameraAngleSelect")

        self.gridLayout.addWidget(self.cameraAngleSelect, 13, 1, 1, 1)

        self.label_29 = QLabel(self.rightWidgetPage1)
        self.label_29.setObjectName(u"label_29")

        self.gridLayout.addWidget(self.label_29, 14, 0, 1, 1)

        self.cameraEffectSelect = QComboBox(self.rightWidgetPage1)
        self.cameraEffectSelect.setObjectName(u"cameraEffectSelect")

        self.gridLayout.addWidget(self.cameraEffectSelect, 14, 1, 1, 1)

        self.script1Label = QLabel(self.rightWidgetPage1)
        self.script1Label.setObjectName(u"script1Label")

        self.gridLayout.addWidget(self.script1Label, 15, 0, 1, 2)

        self.script1ResrefEdit = FilterComboBox(self.rightWidgetPage1)
        self.script1ResrefEdit.setObjectName(u"script1ResrefEdit")

        self.gridLayout.addWidget(self.script1ResrefEdit, 16, 0, 1, 2)

        self.script1Param1Spin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.script1Param1Spin.setObjectName(u"script1Param1Spin")
        self.script1Param1Spin.setMinimum(-2147483647)
        self.script1Param1Spin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.script1Param1Spin, 17, 0, 1, 1)

        self.script1Param2Spin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.script1Param2Spin.setObjectName(u"script1Param2Spin")
        self.script1Param2Spin.setMinimum(-2147483647)
        self.script1Param2Spin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.script1Param2Spin, 17, 1, 1, 1)

        self.script1Param3Spin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.script1Param3Spin.setObjectName(u"script1Param3Spin")
        self.script1Param3Spin.setMinimum(-2147483647)
        self.script1Param3Spin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.script1Param3Spin, 18, 0, 1, 1)

        self.script1Param4Spin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.script1Param4Spin.setObjectName(u"script1Param4Spin")
        self.script1Param4Spin.setMinimum(-2147483647)
        self.script1Param4Spin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.script1Param4Spin, 18, 1, 1, 1)

        self.script1Param5Spin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.script1Param5Spin.setObjectName(u"script1Param5Spin")
        self.script1Param5Spin.setMinimum(-2147483647)
        self.script1Param5Spin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.script1Param5Spin, 19, 0, 1, 1)

        self.script1Param6Edit = QLineEdit(self.rightWidgetPage1)
        self.script1Param6Edit.setObjectName(u"script1Param6Edit")

        self.gridLayout.addWidget(self.script1Param6Edit, 19, 1, 1, 1)

        self.script2Label = QLabel(self.rightWidgetPage1)
        self.script2Label.setObjectName(u"script2Label")

        self.gridLayout.addWidget(self.script2Label, 20, 0, 1, 2)

        self.script2ResrefEdit = FilterComboBox(self.rightWidgetPage1)
        self.script2ResrefEdit.setObjectName(u"script2ResrefEdit")

        self.gridLayout.addWidget(self.script2ResrefEdit, 21, 0, 1, 2)

        self.script2Param1Spin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.script2Param1Spin.setObjectName(u"script2Param1Spin")
        self.script2Param1Spin.setMinimum(-2147483647)
        self.script2Param1Spin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.script2Param1Spin, 22, 0, 1, 1)

        self.script2Param2Spin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.script2Param2Spin.setObjectName(u"script2Param2Spin")
        self.script2Param2Spin.setMinimum(-2147483647)
        self.script2Param2Spin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.script2Param2Spin, 22, 1, 1, 1)

        self.script2Param3Spin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.script2Param3Spin.setObjectName(u"script2Param3Spin")
        self.script2Param3Spin.setMinimum(-2147483647)
        self.script2Param3Spin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.script2Param3Spin, 23, 0, 1, 1)

        self.script2Param4Spin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.script2Param4Spin.setObjectName(u"script2Param4Spin")
        self.script2Param4Spin.setMinimum(-2147483647)
        self.script2Param4Spin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.script2Param4Spin, 23, 1, 1, 1)

        self.script2Param5Spin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.script2Param5Spin.setObjectName(u"script2Param5Spin")
        self.script2Param5Spin.setMinimum(-2147483647)
        self.script2Param5Spin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.script2Param5Spin, 24, 0, 1, 1)

        self.script2Param6Edit = QLineEdit(self.rightWidgetPage1)
        self.script2Param6Edit.setObjectName(u"script2Param6Edit")

        self.gridLayout.addWidget(self.script2Param6Edit, 24, 1, 1, 1)

        self.conditional1Label = QLabel(self.rightWidgetPage1)
        self.conditional1Label.setObjectName(u"conditional1Label")

        self.gridLayout.addWidget(self.conditional1Label, 25, 0, 1, 2)

        self.condition1ResrefEdit = FilterComboBox(self.rightWidgetPage1)
        self.condition1ResrefEdit.setObjectName(u"condition1ResrefEdit")

        self.gridLayout.addWidget(self.condition1ResrefEdit, 26, 0, 1, 1)

        self.condition1Param1Spin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.condition1Param1Spin.setObjectName(u"condition1Param1Spin")
        self.condition1Param1Spin.setMinimum(-2147483647)
        self.condition1Param1Spin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.condition1Param1Spin, 26, 1, 1, 1)

        self.condition1Param2Spin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.condition1Param2Spin.setObjectName(u"condition1Param2Spin")
        self.condition1Param2Spin.setMinimum(-2147483647)
        self.condition1Param2Spin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.condition1Param2Spin, 27, 0, 1, 1)

        self.condition1NotCheckbox = QCheckBox(self.rightWidgetPage1)
        self.condition1NotCheckbox.setObjectName(u"condition1NotCheckbox")

        self.gridLayout.addWidget(self.condition1NotCheckbox, 27, 1, 1, 1)

        self.condition1Param3Spin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.condition1Param3Spin.setObjectName(u"condition1Param3Spin")
        self.condition1Param3Spin.setMinimum(-2147483647)
        self.condition1Param3Spin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.condition1Param3Spin, 28, 0, 1, 1)

        self.condition1Param4Spin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.condition1Param4Spin.setObjectName(u"condition1Param4Spin")
        self.condition1Param4Spin.setMinimum(-2147483647)
        self.condition1Param4Spin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.condition1Param4Spin, 28, 1, 1, 1)

        self.condition1Param5Spin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.condition1Param5Spin.setObjectName(u"condition1Param5Spin")
        self.condition1Param5Spin.setMinimum(-2147483647)
        self.condition1Param5Spin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.condition1Param5Spin, 29, 0, 1, 1)

        self.condition1Param6Edit = QLineEdit(self.rightWidgetPage1)
        self.condition1Param6Edit.setObjectName(u"condition1Param6Edit")

        self.gridLayout.addWidget(self.condition1Param6Edit, 29, 1, 1, 1)

        self.conditional2Label = QLabel(self.rightWidgetPage1)
        self.conditional2Label.setObjectName(u"conditional2Label")

        self.gridLayout.addWidget(self.conditional2Label, 30, 0, 1, 2)

        self.condition2ResrefEdit = FilterComboBox(self.rightWidgetPage1)
        self.condition2ResrefEdit.setObjectName(u"condition2ResrefEdit")

        self.gridLayout.addWidget(self.condition2ResrefEdit, 31, 0, 1, 1)

        self.condition2Param1Spin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.condition2Param1Spin.setObjectName(u"condition2Param1Spin")
        self.condition2Param1Spin.setMinimum(-2147483647)
        self.condition2Param1Spin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.condition2Param1Spin, 31, 1, 1, 1)

        self.condition2Param2Spin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.condition2Param2Spin.setObjectName(u"condition2Param2Spin")
        self.condition2Param2Spin.setMinimum(-2147483647)
        self.condition2Param2Spin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.condition2Param2Spin, 32, 0, 1, 1)

        self.condition2NotCheckbox = QCheckBox(self.rightWidgetPage1)
        self.condition2NotCheckbox.setObjectName(u"condition2NotCheckbox")

        self.gridLayout.addWidget(self.condition2NotCheckbox, 32, 1, 1, 1)

        self.condition2Param3Spin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.condition2Param3Spin.setObjectName(u"condition2Param3Spin")
        self.condition2Param3Spin.setMinimum(-2147483647)
        self.condition2Param3Spin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.condition2Param3Spin, 33, 0, 1, 1)

        self.condition2Param4Spin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.condition2Param4Spin.setObjectName(u"condition2Param4Spin")
        self.condition2Param4Spin.setMinimum(-2147483647)
        self.condition2Param4Spin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.condition2Param4Spin, 33, 1, 1, 1)

        self.condition2Param5Spin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.condition2Param5Spin.setObjectName(u"condition2Param5Spin")
        self.condition2Param5Spin.setMinimum(-2147483647)
        self.condition2Param5Spin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.condition2Param5Spin, 34, 0, 1, 1)

        self.condition2Param6Edit = QLineEdit(self.rightWidgetPage1)
        self.condition2Param6Edit.setObjectName(u"condition2Param6Edit")

        self.gridLayout.addWidget(self.condition2Param6Edit, 34, 1, 1, 1)

        self.label_12 = QLabel(self.rightWidgetPage1)
        self.label_12.setObjectName(u"label_12")

        self.gridLayout.addWidget(self.label_12, 35, 0, 1, 2)

        self.animsList = QListWidget(self.rightWidgetPage1)
        self.animsList.setObjectName(u"animsList")

        self.gridLayout.addWidget(self.animsList, 36, 0, 1, 2)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.addAnimButton = QPushButton(self.rightWidgetPage1)
        self.addAnimButton.setObjectName(u"addAnimButton")

        self.verticalLayout_4.addWidget(self.addAnimButton)

        self.removeAnimButton = QPushButton(self.rightWidgetPage1)
        self.removeAnimButton.setObjectName(u"removeAnimButton")

        self.verticalLayout_4.addWidget(self.removeAnimButton)

        self.editAnimButton = QPushButton(self.rightWidgetPage1)
        self.editAnimButton.setObjectName(u"editAnimButton")

        self.verticalLayout_4.addWidget(self.editAnimButton)


        self.gridLayout.addLayout(self.verticalLayout_4, 37, 0, 1, 2)

        self.label_34 = QLabel(self.rightWidgetPage1)
        self.label_34.setObjectName(u"label_34")

        self.gridLayout.addWidget(self.label_34, 38, 0, 1, 2)

        self.expressionSelect = ComboBox2DA(self.rightWidgetPage1)
        self.expressionSelect.setObjectName(u"expressionSelect")

        self.gridLayout.addWidget(self.expressionSelect, 39, 0, 1, 1)

        self.emotionSelect = ComboBox2DA(self.rightWidgetPage1)
        self.emotionSelect.setObjectName(u"emotionSelect")

        self.gridLayout.addWidget(self.emotionSelect, 39, 1, 1, 1)

        self.label_33 = QLabel(self.rightWidgetPage1)
        self.label_33.setObjectName(u"label_33")

        self.gridLayout.addWidget(self.label_33, 40, 0, 1, 1)

        self.postProcSpin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.postProcSpin.setObjectName(u"postProcSpin")
        self.postProcSpin.setMinimum(-1)
        self.postProcSpin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.postProcSpin, 40, 1, 1, 1)

        self.line = QFrame(self.rightWidgetPage1)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.gridLayout.addWidget(self.line, 41, 0, 1, 2)

        self.label_20 = QLabel(self.rightWidgetPage1)
        self.label_20.setObjectName(u"label_20")

        self.gridLayout.addWidget(self.label_20, 42, 0, 1, 1)

        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.voiceComboBox = FilterComboBox(self.rightWidgetPage1)
        self.voiceComboBox.setObjectName(u"voiceComboBox")

        self.verticalLayout_6.addWidget(self.voiceComboBox)

        self.voiceButton = QPushButton(self.rightWidgetPage1)
        self.voiceButton.setObjectName(u"voiceButton")

        self.verticalLayout_6.addWidget(self.voiceButton)


        self.gridLayout.addLayout(self.verticalLayout_6, 42, 1, 1, 1)

        self.label_19 = QLabel(self.rightWidgetPage1)
        self.label_19.setObjectName(u"label_19")

        self.gridLayout.addWidget(self.label_19, 43, 0, 1, 1)

        self.verticalLayout_8 = QVBoxLayout()
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.soundComboBox = FilterComboBox(self.rightWidgetPage1)
        self.soundComboBox.setObjectName(u"soundComboBox")

        self.verticalLayout_8.addWidget(self.soundComboBox)

        self.soundButton = QPushButton(self.rightWidgetPage1)
        self.soundButton.setObjectName(u"soundButton")

        self.verticalLayout_8.addWidget(self.soundButton)


        self.gridLayout.addLayout(self.verticalLayout_8, 43, 1, 1, 1)

        self.soundCheckbox = QCheckBox(self.rightWidgetPage1)
        self.soundCheckbox.setObjectName(u"soundCheckbox")

        self.gridLayout.addWidget(self.soundCheckbox, 44, 0, 1, 2)

        self.label_36 = QLabel(self.rightWidgetPage1)
        self.label_36.setObjectName(u"label_36")

        self.gridLayout.addWidget(self.label_36, 45, 0, 1, 1)

        self.fadeTypeSpin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.fadeTypeSpin.setObjectName(u"fadeTypeSpin")
        self.fadeTypeSpin.setMinimum(-1)
        self.fadeTypeSpin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.fadeTypeSpin, 45, 1, 1, 1)

        self.label_35 = QLabel(self.rightWidgetPage1)
        self.label_35.setObjectName(u"label_35")

        self.gridLayout.addWidget(self.label_35, 46, 0, 1, 1)

        self.waitFlagSpin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.waitFlagSpin.setObjectName(u"waitFlagSpin")
        self.waitFlagSpin.setMinimum(-1)
        self.waitFlagSpin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.waitFlagSpin, 46, 1, 1, 1)

        self.label_31 = QLabel(self.rightWidgetPage1)
        self.label_31.setObjectName(u"label_31")

        self.gridLayout.addWidget(self.label_31, 47, 0, 1, 1)

        self.alienRaceNodeSpin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.alienRaceNodeSpin.setObjectName(u"alienRaceNodeSpin")
        self.alienRaceNodeSpin.setMinimum(-1)
        self.alienRaceNodeSpin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.alienRaceNodeSpin, 47, 1, 1, 1)

        self.label_32 = QLabel(self.rightWidgetPage1)
        self.label_32.setObjectName(u"label_32")

        self.gridLayout.addWidget(self.label_32, 48, 0, 1, 1)

        self.nodeIdSpin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.nodeIdSpin.setObjectName(u"nodeIdSpin")
        self.nodeIdSpin.setMaximum(999999)

        self.gridLayout.addWidget(self.nodeIdSpin, 48, 1, 1, 1)

        self.label_30 = QLabel(self.rightWidgetPage1)
        self.label_30.setObjectName(u"label_30")

        self.gridLayout.addWidget(self.label_30, 49, 0, 1, 1)

        self.postProcSpin1 = GFFFieldSpinBox(self.rightWidgetPage1)
        self.postProcSpin1.setObjectName(u"postProcSpin1")

        self.gridLayout.addWidget(self.postProcSpin1, 49, 1, 1, 1)

        self.label_331 = QLabel(self.rightWidgetPage1)
        self.label_331.setObjectName(u"label_331")

        self.gridLayout.addWidget(self.label_331, 50, 0, 1, 2)

        self.logicSpin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.logicSpin.setObjectName(u"logicSpin")
        self.logicSpin.setMinimum(-1)
        self.logicSpin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.logicSpin, 51, 0, 1, 1)

        self.expressionSelect1 = ComboBox2DA(self.rightWidgetPage1)
        self.expressionSelect1.setObjectName(u"expressionSelect1")

        self.gridLayout.addWidget(self.expressionSelect1, 51, 1, 1, 1)

        self.label_18 = QLabel(self.rightWidgetPage1)
        self.label_18.setObjectName(u"label_18")

        self.gridLayout.addWidget(self.label_18, 52, 0, 1, 1)

        self.emotionSelect1 = ComboBox2DA(self.rightWidgetPage1)
        self.emotionSelect1.setObjectName(u"emotionSelect1")

        self.gridLayout.addWidget(self.emotionSelect1, 52, 1, 1, 1)

        self.label_191 = QLabel(self.rightWidgetPage1)
        self.label_191.setObjectName(u"label_191")

        self.gridLayout.addWidget(self.label_191, 53, 0, 1, 1)

        self.emotionSelect2 = ComboBox2DA(self.rightWidgetPage1)
        self.emotionSelect2.setObjectName(u"emotionSelect2")

        self.gridLayout.addWidget(self.emotionSelect2, 53, 1, 1, 1)

        self.label_201 = QLabel(self.rightWidgetPage1)
        self.label_201.setObjectName(u"label_201")

        self.gridLayout.addWidget(self.label_201, 54, 0, 1, 1)

        self.verticalLayout_61 = QVBoxLayout()
        self.verticalLayout_61.setObjectName(u"verticalLayout_61")
        self.voiceComboBox1 = FilterComboBox(self.rightWidgetPage1)
        self.voiceComboBox1.setObjectName(u"voiceComboBox1")

        self.verticalLayout_61.addWidget(self.voiceComboBox1)

        self.voiceButton1 = QPushButton(self.rightWidgetPage1)
        self.voiceButton1.setObjectName(u"voiceButton1")

        self.verticalLayout_61.addWidget(self.voiceButton1)


        self.gridLayout.addLayout(self.verticalLayout_61, 54, 1, 1, 1)

        self.label_361 = QLabel(self.rightWidgetPage1)
        self.label_361.setObjectName(u"label_361")

        self.gridLayout.addWidget(self.label_361, 55, 0, 1, 1)

        self.fadeTypeSpin1 = GFFFieldSpinBox(self.rightWidgetPage1)
        self.fadeTypeSpin1.setObjectName(u"fadeTypeSpin1")
        self.fadeTypeSpin1.setMinimum(-1)
        self.fadeTypeSpin1.setMaximum(2147483647)

        self.gridLayout.addWidget(self.fadeTypeSpin1, 55, 1, 1, 1)

        self.label_351 = QLabel(self.rightWidgetPage1)
        self.label_351.setObjectName(u"label_351")

        self.gridLayout.addWidget(self.label_351, 56, 0, 1, 1)

        self.waitFlagSpin1 = GFFFieldSpinBox(self.rightWidgetPage1)
        self.waitFlagSpin1.setObjectName(u"waitFlagSpin1")
        self.waitFlagSpin1.setMinimum(-1)
        self.waitFlagSpin1.setMaximum(2147483647)

        self.gridLayout.addWidget(self.waitFlagSpin1, 56, 1, 1, 1)

        self.label_341 = QLabel(self.rightWidgetPage1)
        self.label_341.setObjectName(u"label_341")

        self.gridLayout.addWidget(self.label_341, 57, 0, 1, 1)

        self.postProcSpin2 = GFFFieldSpinBox(self.rightWidgetPage1)
        self.postProcSpin2.setObjectName(u"postProcSpin2")
        self.postProcSpin2.setMinimum(-1)
        self.postProcSpin2.setMaximum(2147483647)

        self.gridLayout.addWidget(self.postProcSpin2, 57, 1, 1, 1)

        self.soundCheckbox1 = QCheckBox(self.rightWidgetPage1)
        self.soundCheckbox1.setObjectName(u"soundCheckbox1")

        self.gridLayout.addWidget(self.soundCheckbox1, 58, 0, 1, 1)

        self.unequipHandsCheckbox = QCheckBox(self.rightWidgetPage1)
        self.unequipHandsCheckbox.setObjectName(u"unequipHandsCheckbox")

        self.gridLayout.addWidget(self.unequipHandsCheckbox, 59, 0, 1, 1)

        self.unequipAllCheckbox = QCheckBox(self.rightWidgetPage1)
        self.unequipAllCheckbox.setObjectName(u"unequipAllCheckbox")

        self.gridLayout.addWidget(self.unequipAllCheckbox, 60, 0, 1, 1)

        self.label_44 = QLabel(self.rightWidgetPage1)
        self.label_44.setObjectName(u"label_44")

        self.gridLayout.addWidget(self.label_44, 61, 0, 1, 1)

        self.entryDelaySpin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.entryDelaySpin.setObjectName(u"entryDelaySpin")
        self.entryDelaySpin.setMinimum(-2147483648)
        self.entryDelaySpin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.entryDelaySpin, 61, 1, 1, 1)

        self.label_45 = QLabel(self.rightWidgetPage1)
        self.label_45.setObjectName(u"label_45")

        self.gridLayout.addWidget(self.label_45, 62, 0, 1, 1)

        self.replyDelaySpin = GFFFieldSpinBox(self.rightWidgetPage1)
        self.replyDelaySpin.setObjectName(u"replyDelaySpin")
        self.replyDelaySpin.setMinimum(-2147483648)
        self.replyDelaySpin.setMaximum(2147483647)

        self.gridLayout.addWidget(self.replyDelaySpin, 62, 1, 1, 1)

        self.commentsEdit = QPlainTextEdit(self.rightWidgetPage1)
        self.commentsEdit.setObjectName(u"commentsEdit")

        self.gridLayout.addWidget(self.commentsEdit, 63, 0, 1, 2)

        self.scrollArea.setWidget(self.rightWidgetPage1)
        self.rightWidget.addWidget(self.scrollArea)
        self.splitter.addWidget(self.rightWidget)

        self.gridLayout_2.addWidget(self.splitter, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 4095, 21))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuTools = QMenu(self.menubar)
        self.menuTools.setObjectName(u"menuTools")
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
        self.actionReloadTree.setText(QCoreApplication.translate("MainWindow", u"Reload Tree", None))
        self.actionUnfocus.setText(QCoreApplication.translate("MainWindow", u"Unfocus Tree", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Speaker Tag:", None))
        self.label_21.setText(QCoreApplication.translate("MainWindow", u"Listener Tag:", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Text/StringRef:", None))
        self.label_37.setText(QCoreApplication.translate("MainWindow", u"Conversation Ends Script:", None))
        self.label_38.setText(QCoreApplication.translate("MainWindow", u"Conversation Aborts Script:", None))
        self.label_39.setText(QCoreApplication.translate("MainWindow", u"Voiceover ID:", None))
        self.label_42.setText(QCoreApplication.translate("MainWindow", u"Conversation Type:", None))
        self.conversationSelect.setItemText(0, QCoreApplication.translate("MainWindow", u"Human", None))
        self.conversationSelect.setItemText(1, QCoreApplication.translate("MainWindow", u"Computer", None))
        self.conversationSelect.setItemText(2, QCoreApplication.translate("MainWindow", u"Type 3", None))
        self.conversationSelect.setItemText(3, QCoreApplication.translate("MainWindow", u"Type 4", None))
        self.conversationSelect.setItemText(4, QCoreApplication.translate("MainWindow", u"Type 5", None))

        self.label_43.setText(QCoreApplication.translate("MainWindow", u"Computer Type:", None))
        self.computerSelect.setItemText(0, QCoreApplication.translate("MainWindow", u"Modern", None))
        self.computerSelect.setItemText(1, QCoreApplication.translate("MainWindow", u"Ancient", None))

        self.label_41.setText(QCoreApplication.translate("MainWindow", u"Camera Model:", None))
        self.label_40.setText(QCoreApplication.translate("MainWindow", u"Ambient Track:", None))
        self.label_22.setText(QCoreApplication.translate("MainWindow", u"Plot Index:", None))
        self.label_23.setText(QCoreApplication.translate("MainWindow", u"Plot XP Percentage:", None))
        self.label_24.setText(QCoreApplication.translate("MainWindow", u"Quest:", None))
        self.label_25.setText(QCoreApplication.translate("MainWindow", u"Quest Entry:", None))
        self.label_26.setText(QCoreApplication.translate("MainWindow", u"Camera ID:", None))
        self.label_27.setText(QCoreApplication.translate("MainWindow", u"Camera Animation:", None))
        self.label_28.setText(QCoreApplication.translate("MainWindow", u"Camera Angle:", None))
        self.cameraAngleSelect.setItemText(0, QCoreApplication.translate("MainWindow", u"Auto", None))
        self.cameraAngleSelect.setItemText(1, QCoreApplication.translate("MainWindow", u"Face", None))
        self.cameraAngleSelect.setItemText(2, QCoreApplication.translate("MainWindow", u"Shoulder", None))
        self.cameraAngleSelect.setItemText(3, QCoreApplication.translate("MainWindow", u"Wide Shot", None))
        self.cameraAngleSelect.setItemText(4, QCoreApplication.translate("MainWindow", u"Animated Camera", None))
        self.cameraAngleSelect.setItemText(5, QCoreApplication.translate("MainWindow", u"No Change", None))
        self.cameraAngleSelect.setItemText(6, QCoreApplication.translate("MainWindow", u"Static Camera", None))

        self.label_29.setText(QCoreApplication.translate("MainWindow", u"Camera Video Effect:", None))
        self.script1Label.setText(QCoreApplication.translate("MainWindow", u"Script #1:", None))
        self.script2Label.setText(QCoreApplication.translate("MainWindow", u"Script #2:", None))
        self.conditional1Label.setText(QCoreApplication.translate("MainWindow", u"Conditional #1:", None))
        self.condition1NotCheckbox.setText(QCoreApplication.translate("MainWindow", u"Not", None))
        self.conditional2Label.setText(QCoreApplication.translate("MainWindow", u"Conditional #2:", None))
        self.condition2NotCheckbox.setText(QCoreApplication.translate("MainWindow", u"Not", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", u"Current Animations", None))
        self.addAnimButton.setText(QCoreApplication.translate("MainWindow", u"Add", None))
        self.removeAnimButton.setText(QCoreApplication.translate("MainWindow", u"Remove", None))
        self.editAnimButton.setText(QCoreApplication.translate("MainWindow", u"Edit", None))
        self.label_34.setText(QCoreApplication.translate("MainWindow", u"Logic:", None))
        self.label_33.setText(QCoreApplication.translate("MainWindow", u"Post Proc Node:", None))
        self.label_20.setText(QCoreApplication.translate("MainWindow", u"Voice:", None))
        self.voiceButton.setText(QCoreApplication.translate("MainWindow", u"Play", None))
        self.label_19.setText(QCoreApplication.translate("MainWindow", u"Sound:", None))
        self.soundButton.setText(QCoreApplication.translate("MainWindow", u"Play", None))
        self.soundCheckbox.setText(QCoreApplication.translate("MainWindow", u"Enabled", None))
        self.label_36.setText(QCoreApplication.translate("MainWindow", u"Fade Type:", None))
        self.label_35.setText(QCoreApplication.translate("MainWindow", u"Wait Flags:", None))
        self.label_31.setText(QCoreApplication.translate("MainWindow", u"Alien Race Node:", None))
        self.label_32.setText(QCoreApplication.translate("MainWindow", u"Node ID:", None))
        self.label_30.setText(QCoreApplication.translate("MainWindow", u"Post Proc Node:", None))
        self.label_331.setText(QCoreApplication.translate("MainWindow", u"Logic:", None))
        self.label_18.setText(QCoreApplication.translate("MainWindow", u"Expression:", None))
        self.label_191.setText(QCoreApplication.translate("MainWindow", u"Emotion:", None))
        self.label_201.setText(QCoreApplication.translate("MainWindow", u"Voice:", None))
        self.voiceButton1.setText(QCoreApplication.translate("MainWindow", u"Play", None))
        self.label_361.setText(QCoreApplication.translate("MainWindow", u"Fade Type:", None))
        self.label_351.setText(QCoreApplication.translate("MainWindow", u"Wait Flags:", None))
        self.label_341.setText(QCoreApplication.translate("MainWindow", u"Post Proc Node:", None))
        self.soundCheckbox1.setText(QCoreApplication.translate("MainWindow", u"Enabled", None))
        self.unequipHandsCheckbox.setText(QCoreApplication.translate("MainWindow", u"Unequip Hands", None))
        self.unequipAllCheckbox.setText(QCoreApplication.translate("MainWindow", u"Unequip All", None))
        self.label_44.setText(QCoreApplication.translate("MainWindow", u"Delay before entry:", None))
        self.label_45.setText(QCoreApplication.translate("MainWindow", u"Delay before reply:", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuTools.setTitle(QCoreApplication.translate("MainWindow", u"Tools", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
