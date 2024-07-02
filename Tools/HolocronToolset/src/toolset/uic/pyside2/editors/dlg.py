# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dlg.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from toolset.gui.widgets.edit.combobox_2da import ComboBox2DA
from toolset.gui.common.widgets.combobox import FilterComboBox
from toolset.gui.editors.dlg import DLGTreeView
from toolset.gui.widgets.edit.spinbox import GFFFieldSpinBox


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1286, 694)
        MainWindow.setMouseTracking(True)
        MainWindow.setDockNestingEnabled(True)
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
        self.centralwidget.setMouseTracking(True)
        self.verticalLayout_main = QVBoxLayout(self.centralwidget)
        self.verticalLayout_main.setSpacing(6)
        self.verticalLayout_main.setObjectName(u"verticalLayout_main")
        self.verticalLayout_main.setContentsMargins(2, 2, 2, 2)
        self.horizontalLayout_main = QHBoxLayout()
        self.horizontalLayout_main.setSpacing(0)
        self.horizontalLayout_main.setObjectName(u"horizontalLayout_main")
        self.dialogTree = DLGTreeView(self.centralwidget)
        self.dialogTree.setObjectName(u"dialogTree")
        self.dialogTree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.dialogTree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dialogTree.setExpandsOnDoubleClick(False)

        self.horizontalLayout_main.addWidget(self.dialogTree)


        self.verticalLayout_main.addLayout(self.horizontalLayout_main)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setHorizontalSpacing(5)
        self.gridLayout.setContentsMargins(3, 0, 3, 0)
        self.questEdit = QLineEdit(self.centralwidget)
        self.questEdit.setObjectName(u"questEdit")
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.questEdit.sizePolicy().hasHeightForWidth())
        self.questEdit.setSizePolicy(sizePolicy)
        self.questEdit.setMinimumSize(QSize(150, 0))
        self.questEdit.setMaximumSize(QSize(250, 16777215))

        self.gridLayout.addWidget(self.questEdit, 0, 3, 1, 1)

        self.plotXpSpin = QDoubleSpinBox(self.centralwidget)
        self.plotXpSpin.setObjectName(u"plotXpSpin")
        sizePolicy.setHeightForWidth(self.plotXpSpin.sizePolicy().hasHeightForWidth())
        self.plotXpSpin.setSizePolicy(sizePolicy)
        self.plotXpSpin.setMinimumSize(QSize(150, 0))
        self.plotXpSpin.setMaximumSize(QSize(250, 16777215))

        self.gridLayout.addWidget(self.plotXpSpin, 2, 1, 1, 1)

        self.questEntryLabel = QLabel(self.centralwidget)
        self.questEntryLabel.setObjectName(u"questEntryLabel")

        self.gridLayout.addWidget(self.questEntryLabel, 1, 2, 1, 1, Qt.AlignRight)

        self.questLabel = QLabel(self.centralwidget)
        self.questLabel.setObjectName(u"questLabel")

        self.gridLayout.addWidget(self.questLabel, 0, 2, 1, 1, Qt.AlignRight)

        self.listenerEdit = QLineEdit(self.centralwidget)
        self.listenerEdit.setObjectName(u"listenerEdit")
        sizePolicy.setHeightForWidth(self.listenerEdit.sizePolicy().hasHeightForWidth())
        self.listenerEdit.setSizePolicy(sizePolicy)
        self.listenerEdit.setMinimumSize(QSize(150, 0))
        self.listenerEdit.setMaximumSize(QSize(250, 16777215))

        self.gridLayout.addWidget(self.listenerEdit, 0, 1, 1, 1)

        self.listenerTagLabel = QLabel(self.centralwidget)
        self.listenerTagLabel.setObjectName(u"listenerTagLabel")
        sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.listenerTagLabel.sizePolicy().hasHeightForWidth())
        self.listenerTagLabel.setSizePolicy(sizePolicy1)

        self.gridLayout.addWidget(self.listenerTagLabel, 0, 0, 1, 1, Qt.AlignRight|Qt.AlignVCenter)

        self.speakerEdit = QLineEdit(self.centralwidget)
        self.speakerEdit.setObjectName(u"speakerEdit")
        sizePolicy.setHeightForWidth(self.speakerEdit.sizePolicy().hasHeightForWidth())
        self.speakerEdit.setSizePolicy(sizePolicy)
        self.speakerEdit.setMinimumSize(QSize(150, 0))
        self.speakerEdit.setMaximumSize(QSize(250, 16777215))

        self.gridLayout.addWidget(self.speakerEdit, 1, 1, 1, 1)

        self.questEntrySpin = GFFFieldSpinBox(self.centralwidget)
        self.questEntrySpin.setObjectName(u"questEntrySpin")
        self.questEntrySpin.setMinimumSize(QSize(150, 0))
        self.questEntrySpin.setMaximumSize(QSize(250, 16777215))

        self.gridLayout.addWidget(self.questEntrySpin, 1, 3, 1, 1)

        self.speakerEditLabel = QLabel(self.centralwidget)
        self.speakerEditLabel.setObjectName(u"speakerEditLabel")

        self.gridLayout.addWidget(self.speakerEditLabel, 1, 0, 1, 1, Qt.AlignRight|Qt.AlignVCenter)

        self.plotXpPercentLabel = QLabel(self.centralwidget)
        self.plotXpPercentLabel.setObjectName(u"plotXpPercentLabel")

        self.gridLayout.addWidget(self.plotXpPercentLabel, 2, 0, 1, 1, Qt.AlignRight)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 1, 4, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_2, 0, 4, 1, 1)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_3, 2, 4, 1, 1)

        self.plotIndexLabel = QLabel(self.centralwidget)
        self.plotIndexLabel.setObjectName(u"plotIndexLabel")

        self.gridLayout.addWidget(self.plotIndexLabel, 2, 2, 1, 1, Qt.AlignRight)

        self.plotIndexCombo = ComboBox2DA(self.centralwidget)
        self.plotIndexCombo.setObjectName(u"plotIndexCombo")

        self.gridLayout.addWidget(self.plotIndexCombo, 2, 3, 1, 1)


        self.verticalLayout_main.addLayout(self.gridLayout)

        MainWindow.setCentralWidget(self.centralwidget)
        self.rightDockWidget = QDockWidget(MainWindow)
        self.rightDockWidget.setObjectName(u"rightDockWidget")
        self.rightDockWidget.setMinimumSize(QSize(310, 100))
        self.rightDockWidget.setBaseSize(QSize(310, 100))
        self.rightDockWidget.setFloating(False)
        self.rightDockWidget.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.scrollArea_rightDock = QScrollArea()
        self.scrollArea_rightDock.setObjectName(u"scrollArea_rightDock")
        self.scrollArea_rightDock.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 305, 970))
        self.verticalLayout_rightDock = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_rightDock.setSpacing(0)
        self.verticalLayout_rightDock.setObjectName(u"verticalLayout_rightDock")
        self.verticalLayout_rightDock.setContentsMargins(0, 0, 2, 0)
        self.verticalLayout_scripts = QVBoxLayout()
        self.verticalLayout_scripts.setSpacing(0)
        self.verticalLayout_scripts.setObjectName(u"verticalLayout_scripts")
        self.verticalLayout_scripts.setContentsMargins(0, 0, 0, 0)
        self.commentsEdit = QPlainTextEdit(self.scrollAreaWidgetContents)
        self.commentsEdit.setObjectName(u"commentsEdit")

        self.verticalLayout_scripts.addWidget(self.commentsEdit)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.script1Label = QLabel(self.scrollAreaWidgetContents)
        self.script1Label.setObjectName(u"script1Label")
        sizePolicy2 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.script1Label.sizePolicy().hasHeightForWidth())
        self.script1Label.setSizePolicy(sizePolicy2)
        self.script1Label.setMinimumSize(QSize(100, 0))
        self.script1Label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout.addWidget(self.script1Label, 0, Qt.AlignLeft)

        self.script1ResrefEdit = FilterComboBox(self.scrollAreaWidgetContents)
        self.script1ResrefEdit.setObjectName(u"script1ResrefEdit")
        sizePolicy3 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.script1ResrefEdit.sizePolicy().hasHeightForWidth())
        self.script1ResrefEdit.setSizePolicy(sizePolicy3)
        self.script1ResrefEdit.setMinimumSize(QSize(150, 0))
        self.script1ResrefEdit.setMaximumSize(QSize(16777215, 16777215))

        self.horizontalLayout.addWidget(self.script1ResrefEdit)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_4)


        self.verticalLayout_scripts.addLayout(self.horizontalLayout)

        self.horizontalLayout_script1Params = QHBoxLayout()
        self.horizontalLayout_script1Params.setSpacing(0)
        self.horizontalLayout_script1Params.setObjectName(u"horizontalLayout_script1Params")
        self.script1Param1Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script1Param1Spin.setObjectName(u"script1Param1Spin")
        sizePolicy3.setHeightForWidth(self.script1Param1Spin.sizePolicy().hasHeightForWidth())
        self.script1Param1Spin.setSizePolicy(sizePolicy3)
        self.script1Param1Spin.setMinimumSize(QSize(30, 0))
        self.script1Param1Spin.setMinimum(-2147483648)
        self.script1Param1Spin.setMaximum(2147483647)

        self.horizontalLayout_script1Params.addWidget(self.script1Param1Spin)

        self.script1Param2Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script1Param2Spin.setObjectName(u"script1Param2Spin")
        sizePolicy3.setHeightForWidth(self.script1Param2Spin.sizePolicy().hasHeightForWidth())
        self.script1Param2Spin.setSizePolicy(sizePolicy3)
        self.script1Param2Spin.setMinimumSize(QSize(30, 0))
        self.script1Param2Spin.setMinimum(-2147483648)
        self.script1Param2Spin.setMaximum(2147483647)

        self.horizontalLayout_script1Params.addWidget(self.script1Param2Spin)

        self.script1Param3Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script1Param3Spin.setObjectName(u"script1Param3Spin")
        sizePolicy3.setHeightForWidth(self.script1Param3Spin.sizePolicy().hasHeightForWidth())
        self.script1Param3Spin.setSizePolicy(sizePolicy3)
        self.script1Param3Spin.setMinimumSize(QSize(30, 0))
        self.script1Param3Spin.setMinimum(-2147483648)
        self.script1Param3Spin.setMaximum(2147483647)

        self.horizontalLayout_script1Params.addWidget(self.script1Param3Spin)

        self.script1Param4Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script1Param4Spin.setObjectName(u"script1Param4Spin")
        sizePolicy3.setHeightForWidth(self.script1Param4Spin.sizePolicy().hasHeightForWidth())
        self.script1Param4Spin.setSizePolicy(sizePolicy3)
        self.script1Param4Spin.setMinimumSize(QSize(30, 0))
        self.script1Param4Spin.setMinimum(-2147483648)
        self.script1Param4Spin.setMaximum(2147483647)

        self.horizontalLayout_script1Params.addWidget(self.script1Param4Spin)

        self.script1Param5Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script1Param5Spin.setObjectName(u"script1Param5Spin")
        sizePolicy4 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.script1Param5Spin.sizePolicy().hasHeightForWidth())
        self.script1Param5Spin.setSizePolicy(sizePolicy4)
        self.script1Param5Spin.setMaximumSize(QSize(85, 16777215))

        self.horizontalLayout_script1Params.addWidget(self.script1Param5Spin)

        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_script1Params.addItem(self.horizontalSpacer_9)

        self.script1Param6Edit = QLineEdit(self.scrollAreaWidgetContents)
        self.script1Param6Edit.setObjectName(u"script1Param6Edit")
        sizePolicy5 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.script1Param6Edit.sizePolicy().hasHeightForWidth())
        self.script1Param6Edit.setSizePolicy(sizePolicy5)
        self.script1Param6Edit.setMinimumSize(QSize(0, 0))

        self.horizontalLayout_script1Params.addWidget(self.script1Param6Edit)


        self.verticalLayout_scripts.addLayout(self.horizontalLayout_script1Params)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.script2Label = QLabel(self.scrollAreaWidgetContents)
        self.script2Label.setObjectName(u"script2Label")
        sizePolicy2.setHeightForWidth(self.script2Label.sizePolicy().hasHeightForWidth())
        self.script2Label.setSizePolicy(sizePolicy2)
        self.script2Label.setMinimumSize(QSize(100, 0))
        self.script2Label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_2.addWidget(self.script2Label, 0, Qt.AlignLeft)

        self.script2ResrefEdit = FilterComboBox(self.scrollAreaWidgetContents)
        self.script2ResrefEdit.setObjectName(u"script2ResrefEdit")
        self.script2ResrefEdit.setMinimumSize(QSize(150, 0))
        self.script2ResrefEdit.setMaximumSize(QSize(16777215, 16777215))

        self.horizontalLayout_2.addWidget(self.script2ResrefEdit)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_5)


        self.verticalLayout_scripts.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_script2Params = QHBoxLayout()
        self.horizontalLayout_script2Params.setSpacing(0)
        self.horizontalLayout_script2Params.setObjectName(u"horizontalLayout_script2Params")
        self.script2Param1Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script2Param1Spin.setObjectName(u"script2Param1Spin")
        sizePolicy3.setHeightForWidth(self.script2Param1Spin.sizePolicy().hasHeightForWidth())
        self.script2Param1Spin.setSizePolicy(sizePolicy3)
        self.script2Param1Spin.setMinimumSize(QSize(30, 0))
        self.script2Param1Spin.setMinimum(-2147483648)
        self.script2Param1Spin.setMaximum(2147483647)

        self.horizontalLayout_script2Params.addWidget(self.script2Param1Spin)

        self.script2Param2Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script2Param2Spin.setObjectName(u"script2Param2Spin")
        sizePolicy3.setHeightForWidth(self.script2Param2Spin.sizePolicy().hasHeightForWidth())
        self.script2Param2Spin.setSizePolicy(sizePolicy3)
        self.script2Param2Spin.setMinimumSize(QSize(30, 0))
        self.script2Param2Spin.setMinimum(-2147483648)
        self.script2Param2Spin.setMaximum(2147483647)

        self.horizontalLayout_script2Params.addWidget(self.script2Param2Spin)

        self.script2Param3Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script2Param3Spin.setObjectName(u"script2Param3Spin")
        sizePolicy3.setHeightForWidth(self.script2Param3Spin.sizePolicy().hasHeightForWidth())
        self.script2Param3Spin.setSizePolicy(sizePolicy3)
        self.script2Param3Spin.setMinimumSize(QSize(30, 0))
        self.script2Param3Spin.setMinimum(-2147483648)
        self.script2Param3Spin.setMaximum(2147483647)

        self.horizontalLayout_script2Params.addWidget(self.script2Param3Spin)

        self.script2Param4Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script2Param4Spin.setObjectName(u"script2Param4Spin")
        sizePolicy3.setHeightForWidth(self.script2Param4Spin.sizePolicy().hasHeightForWidth())
        self.script2Param4Spin.setSizePolicy(sizePolicy3)
        self.script2Param4Spin.setMinimumSize(QSize(30, 0))
        self.script2Param4Spin.setMinimum(-2147483648)
        self.script2Param4Spin.setMaximum(2147483647)

        self.horizontalLayout_script2Params.addWidget(self.script2Param4Spin)

        self.script2Param5Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script2Param5Spin.setObjectName(u"script2Param5Spin")
        sizePolicy3.setHeightForWidth(self.script2Param5Spin.sizePolicy().hasHeightForWidth())
        self.script2Param5Spin.setSizePolicy(sizePolicy3)
        self.script2Param5Spin.setMinimumSize(QSize(30, 0))
        self.script2Param5Spin.setMinimum(-2147483648)
        self.script2Param5Spin.setMaximum(2147483647)

        self.horizontalLayout_script2Params.addWidget(self.script2Param5Spin)

        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_script2Params.addItem(self.horizontalSpacer_8)

        self.script2Param6Edit = QLineEdit(self.scrollAreaWidgetContents)
        self.script2Param6Edit.setObjectName(u"script2Param6Edit")
        sizePolicy5.setHeightForWidth(self.script2Param6Edit.sizePolicy().hasHeightForWidth())
        self.script2Param6Edit.setSizePolicy(sizePolicy5)

        self.horizontalLayout_script2Params.addWidget(self.script2Param6Edit)


        self.verticalLayout_scripts.addLayout(self.horizontalLayout_script2Params)


        self.verticalLayout_rightDock.addLayout(self.verticalLayout_scripts)

        self.verticalLayout_conditions = QVBoxLayout()
        self.verticalLayout_conditions.setSpacing(2)
        self.verticalLayout_conditions.setObjectName(u"verticalLayout_conditions")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(2)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.conditional1Label = QLabel(self.scrollAreaWidgetContents)
        self.conditional1Label.setObjectName(u"conditional1Label")
        sizePolicy2.setHeightForWidth(self.conditional1Label.sizePolicy().hasHeightForWidth())
        self.conditional1Label.setSizePolicy(sizePolicy2)
        self.conditional1Label.setMinimumSize(QSize(100, 0))

        self.horizontalLayout_3.addWidget(self.conditional1Label)

        self.condition1ResrefEdit = FilterComboBox(self.scrollAreaWidgetContents)
        self.condition1ResrefEdit.setObjectName(u"condition1ResrefEdit")
        self.condition1ResrefEdit.setMinimumSize(QSize(150, 0))
        self.condition1ResrefEdit.setMaximumSize(QSize(16777215, 16777215))

        self.horizontalLayout_3.addWidget(self.condition1ResrefEdit)

        self.condition1NotCheckbox = QCheckBox(self.scrollAreaWidgetContents)
        self.condition1NotCheckbox.setObjectName(u"condition1NotCheckbox")

        self.horizontalLayout_3.addWidget(self.condition1NotCheckbox)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_6)


        self.verticalLayout_conditions.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_condition1Params = QHBoxLayout()
        self.horizontalLayout_condition1Params.setSpacing(0)
        self.horizontalLayout_condition1Params.setObjectName(u"horizontalLayout_condition1Params")
        self.condition1Param1Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition1Param1Spin.setObjectName(u"condition1Param1Spin")
        sizePolicy3.setHeightForWidth(self.condition1Param1Spin.sizePolicy().hasHeightForWidth())
        self.condition1Param1Spin.setSizePolicy(sizePolicy3)
        self.condition1Param1Spin.setMinimumSize(QSize(30, 0))
        self.condition1Param1Spin.setMinimum(-2147483648)
        self.condition1Param1Spin.setMaximum(2147483647)

        self.horizontalLayout_condition1Params.addWidget(self.condition1Param1Spin)

        self.condition1Param2Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition1Param2Spin.setObjectName(u"condition1Param2Spin")
        sizePolicy3.setHeightForWidth(self.condition1Param2Spin.sizePolicy().hasHeightForWidth())
        self.condition1Param2Spin.setSizePolicy(sizePolicy3)
        self.condition1Param2Spin.setMinimumSize(QSize(30, 0))
        self.condition1Param2Spin.setMinimum(-2147483648)
        self.condition1Param2Spin.setMaximum(2147483647)

        self.horizontalLayout_condition1Params.addWidget(self.condition1Param2Spin)

        self.condition1Param3Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition1Param3Spin.setObjectName(u"condition1Param3Spin")
        sizePolicy3.setHeightForWidth(self.condition1Param3Spin.sizePolicy().hasHeightForWidth())
        self.condition1Param3Spin.setSizePolicy(sizePolicy3)
        self.condition1Param3Spin.setMinimumSize(QSize(30, 0))
        self.condition1Param3Spin.setMinimum(-2147483648)
        self.condition1Param3Spin.setMaximum(2147483647)

        self.horizontalLayout_condition1Params.addWidget(self.condition1Param3Spin)

        self.condition1Param4Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition1Param4Spin.setObjectName(u"condition1Param4Spin")
        sizePolicy3.setHeightForWidth(self.condition1Param4Spin.sizePolicy().hasHeightForWidth())
        self.condition1Param4Spin.setSizePolicy(sizePolicy3)
        self.condition1Param4Spin.setMinimumSize(QSize(30, 0))
        self.condition1Param4Spin.setMinimum(-2147483648)
        self.condition1Param4Spin.setMaximum(2147483647)

        self.horizontalLayout_condition1Params.addWidget(self.condition1Param4Spin)

        self.condition1Param5Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition1Param5Spin.setObjectName(u"condition1Param5Spin")
        sizePolicy3.setHeightForWidth(self.condition1Param5Spin.sizePolicy().hasHeightForWidth())
        self.condition1Param5Spin.setSizePolicy(sizePolicy3)
        self.condition1Param5Spin.setMinimumSize(QSize(30, 0))
        self.condition1Param5Spin.setMinimum(-2147483648)
        self.condition1Param5Spin.setMaximum(2147483647)

        self.horizontalLayout_condition1Params.addWidget(self.condition1Param5Spin)

        self.condition1Param6Edit = QLineEdit(self.scrollAreaWidgetContents)
        self.condition1Param6Edit.setObjectName(u"condition1Param6Edit")
        sizePolicy5.setHeightForWidth(self.condition1Param6Edit.sizePolicy().hasHeightForWidth())
        self.condition1Param6Edit.setSizePolicy(sizePolicy5)

        self.horizontalLayout_condition1Params.addWidget(self.condition1Param6Edit)


        self.verticalLayout_conditions.addLayout(self.horizontalLayout_condition1Params)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(2)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.conditional2Label = QLabel(self.scrollAreaWidgetContents)
        self.conditional2Label.setObjectName(u"conditional2Label")
        sizePolicy2.setHeightForWidth(self.conditional2Label.sizePolicy().hasHeightForWidth())
        self.conditional2Label.setSizePolicy(sizePolicy2)
        self.conditional2Label.setMinimumSize(QSize(100, 0))

        self.horizontalLayout_4.addWidget(self.conditional2Label)

        self.condition2ResrefEdit = FilterComboBox(self.scrollAreaWidgetContents)
        self.condition2ResrefEdit.setObjectName(u"condition2ResrefEdit")
        self.condition2ResrefEdit.setMinimumSize(QSize(150, 0))
        self.condition2ResrefEdit.setMaximumSize(QSize(16777215, 16777215))

        self.horizontalLayout_4.addWidget(self.condition2ResrefEdit)

        self.condition2NotCheckbox = QCheckBox(self.scrollAreaWidgetContents)
        self.condition2NotCheckbox.setObjectName(u"condition2NotCheckbox")

        self.horizontalLayout_4.addWidget(self.condition2NotCheckbox)

        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_7)


        self.verticalLayout_conditions.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(-1, -1, -1, 0)

        self.verticalLayout_conditions.addLayout(self.horizontalLayout_9)

        self.horizontalLayout_condition2Params = QHBoxLayout()
        self.horizontalLayout_condition2Params.setSpacing(0)
        self.horizontalLayout_condition2Params.setObjectName(u"horizontalLayout_condition2Params")
        self.condition2Param1Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition2Param1Spin.setObjectName(u"condition2Param1Spin")
        sizePolicy3.setHeightForWidth(self.condition2Param1Spin.sizePolicy().hasHeightForWidth())
        self.condition2Param1Spin.setSizePolicy(sizePolicy3)
        self.condition2Param1Spin.setMinimumSize(QSize(30, 0))
        self.condition2Param1Spin.setMinimum(-2147483648)
        self.condition2Param1Spin.setMaximum(2147483647)

        self.horizontalLayout_condition2Params.addWidget(self.condition2Param1Spin)

        self.condition2Param2Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition2Param2Spin.setObjectName(u"condition2Param2Spin")
        sizePolicy3.setHeightForWidth(self.condition2Param2Spin.sizePolicy().hasHeightForWidth())
        self.condition2Param2Spin.setSizePolicy(sizePolicy3)
        self.condition2Param2Spin.setMinimumSize(QSize(30, 0))
        self.condition2Param2Spin.setMinimum(-2147483648)
        self.condition2Param2Spin.setMaximum(2147483647)

        self.horizontalLayout_condition2Params.addWidget(self.condition2Param2Spin)

        self.condition2Param3Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition2Param3Spin.setObjectName(u"condition2Param3Spin")
        sizePolicy3.setHeightForWidth(self.condition2Param3Spin.sizePolicy().hasHeightForWidth())
        self.condition2Param3Spin.setSizePolicy(sizePolicy3)
        self.condition2Param3Spin.setMinimumSize(QSize(30, 0))
        self.condition2Param3Spin.setMinimum(-2147483648)
        self.condition2Param3Spin.setMaximum(2147483647)

        self.horizontalLayout_condition2Params.addWidget(self.condition2Param3Spin)

        self.condition2Param4Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition2Param4Spin.setObjectName(u"condition2Param4Spin")
        sizePolicy3.setHeightForWidth(self.condition2Param4Spin.sizePolicy().hasHeightForWidth())
        self.condition2Param4Spin.setSizePolicy(sizePolicy3)
        self.condition2Param4Spin.setMinimumSize(QSize(30, 0))
        self.condition2Param4Spin.setMinimum(-2147483648)
        self.condition2Param4Spin.setMaximum(2147483647)

        self.horizontalLayout_condition2Params.addWidget(self.condition2Param4Spin)

        self.condition2Param5Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition2Param5Spin.setObjectName(u"condition2Param5Spin")
        sizePolicy3.setHeightForWidth(self.condition2Param5Spin.sizePolicy().hasHeightForWidth())
        self.condition2Param5Spin.setSizePolicy(sizePolicy3)
        self.condition2Param5Spin.setMinimumSize(QSize(30, 0))
        self.condition2Param5Spin.setMinimum(-2147483648)
        self.condition2Param5Spin.setMaximum(2147483647)

        self.horizontalLayout_condition2Params.addWidget(self.condition2Param5Spin)

        self.condition2Param6Edit = QLineEdit(self.scrollAreaWidgetContents)
        self.condition2Param6Edit.setObjectName(u"condition2Param6Edit")
        sizePolicy5.setHeightForWidth(self.condition2Param6Edit.sizePolicy().hasHeightForWidth())
        self.condition2Param6Edit.setSizePolicy(sizePolicy5)

        self.horizontalLayout_condition2Params.addWidget(self.condition2Param6Edit)


        self.verticalLayout_conditions.addLayout(self.horizontalLayout_condition2Params)


        self.verticalLayout_rightDock.addLayout(self.verticalLayout_conditions)

        self.verticalLayout_anims = QVBoxLayout()
        self.verticalLayout_anims.setSpacing(2)
        self.verticalLayout_anims.setObjectName(u"verticalLayout_anims")
        self.curAnimsLabel = QLabel(self.scrollAreaWidgetContents)
        self.curAnimsLabel.setObjectName(u"curAnimsLabel")
        self.curAnimsLabel.setLayoutDirection(Qt.LeftToRight)
        self.curAnimsLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout_anims.addWidget(self.curAnimsLabel, 0, Qt.AlignVCenter)

        self.animsList = QListWidget(self.scrollAreaWidgetContents)
        self.animsList.setObjectName(u"animsList")
        sizePolicy6 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.animsList.sizePolicy().hasHeightForWidth())
        self.animsList.setSizePolicy(sizePolicy6)

        self.verticalLayout_anims.addWidget(self.animsList)

        self.horizontalLayout_animsButtons = QHBoxLayout()
        self.horizontalLayout_animsButtons.setObjectName(u"horizontalLayout_animsButtons")
        self.addAnimButton = QPushButton(self.scrollAreaWidgetContents)
        self.addAnimButton.setObjectName(u"addAnimButton")

        self.horizontalLayout_animsButtons.addWidget(self.addAnimButton)

        self.removeAnimButton = QPushButton(self.scrollAreaWidgetContents)
        self.removeAnimButton.setObjectName(u"removeAnimButton")

        self.horizontalLayout_animsButtons.addWidget(self.removeAnimButton)

        self.editAnimButton = QPushButton(self.scrollAreaWidgetContents)
        self.editAnimButton.setObjectName(u"editAnimButton")

        self.horizontalLayout_animsButtons.addWidget(self.editAnimButton)


        self.verticalLayout_anims.addLayout(self.horizontalLayout_animsButtons)

        self.formLayout_anims = QFormLayout()
        self.formLayout_anims.setObjectName(u"formLayout_anims")
        self.emotionSelect = ComboBox2DA(self.scrollAreaWidgetContents)
        self.emotionSelect.setObjectName(u"emotionSelect")

        self.formLayout_anims.setWidget(0, QFormLayout.FieldRole, self.emotionSelect)

        self.expressionLabel = QLabel(self.scrollAreaWidgetContents)
        self.expressionLabel.setObjectName(u"expressionLabel")

        self.formLayout_anims.setWidget(1, QFormLayout.LabelRole, self.expressionLabel)

        self.expressionSelect = ComboBox2DA(self.scrollAreaWidgetContents)
        self.expressionSelect.setObjectName(u"expressionSelect")

        self.formLayout_anims.setWidget(1, QFormLayout.FieldRole, self.expressionSelect)

        self.emotionLabel = QLabel(self.scrollAreaWidgetContents)
        self.emotionLabel.setObjectName(u"emotionLabel")
        self.emotionLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.formLayout_anims.setWidget(0, QFormLayout.LabelRole, self.emotionLabel)


        self.verticalLayout_anims.addLayout(self.formLayout_anims)

        self.formLayout_sound = QFormLayout()
        self.formLayout_sound.setObjectName(u"formLayout_sound")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, -1, -1)
        self.soundLabel = QLabel(self.scrollAreaWidgetContents)
        self.soundLabel.setObjectName(u"soundLabel")
        sizePolicy3.setHeightForWidth(self.soundLabel.sizePolicy().hasHeightForWidth())
        self.soundLabel.setSizePolicy(sizePolicy3)

        self.verticalLayout_2.addWidget(self.soundLabel, 0, Qt.AlignHCenter)

        self.soundCheckbox = QCheckBox(self.scrollAreaWidgetContents)
        self.soundCheckbox.setObjectName(u"soundCheckbox")
        self.soundCheckbox.setMaximumSize(QSize(250, 16777215))

        self.verticalLayout_2.addWidget(self.soundCheckbox, 0, Qt.AlignHCenter|Qt.AlignTop)


        self.formLayout_sound.setLayout(0, QFormLayout.LabelRole, self.verticalLayout_2)

        self.verticalLayout_sound = QVBoxLayout()
        self.verticalLayout_sound.setSpacing(4)
        self.verticalLayout_sound.setObjectName(u"verticalLayout_sound")
        self.soundComboBox = FilterComboBox(self.scrollAreaWidgetContents)
        self.soundComboBox.setObjectName(u"soundComboBox")

        self.verticalLayout_sound.addWidget(self.soundComboBox)

        self.soundButton = QPushButton(self.scrollAreaWidgetContents)
        self.soundButton.setObjectName(u"soundButton")

        self.verticalLayout_sound.addWidget(self.soundButton)


        self.formLayout_sound.setLayout(0, QFormLayout.FieldRole, self.verticalLayout_sound)

        self.verticalLayout_voice = QVBoxLayout()
        self.verticalLayout_voice.setObjectName(u"verticalLayout_voice")
        self.voiceComboBox = FilterComboBox(self.scrollAreaWidgetContents)
        self.voiceComboBox.setObjectName(u"voiceComboBox")

        self.verticalLayout_voice.addWidget(self.voiceComboBox)

        self.voiceButton = QPushButton(self.scrollAreaWidgetContents)
        self.voiceButton.setObjectName(u"voiceButton")

        self.verticalLayout_voice.addWidget(self.voiceButton)


        self.formLayout_sound.setLayout(2, QFormLayout.FieldRole, self.verticalLayout_voice)

        self.voiceLabel = QLabel(self.scrollAreaWidgetContents)
        self.voiceLabel.setObjectName(u"voiceLabel")

        self.formLayout_sound.setWidget(2, QFormLayout.LabelRole, self.voiceLabel)


        self.verticalLayout_anims.addLayout(self.formLayout_sound)


        self.verticalLayout_rightDock.addLayout(self.verticalLayout_anims)

        self.verticalLayout_journal = QVBoxLayout()
        self.verticalLayout_journal.setObjectName(u"verticalLayout_journal")

        self.verticalLayout_rightDock.addLayout(self.verticalLayout_journal)

        self.verticalLayout_camera = QVBoxLayout()
        self.verticalLayout_camera.setObjectName(u"verticalLayout_camera")
        self.cameraIdLabel = QLabel(self.scrollAreaWidgetContents)
        self.cameraIdLabel.setObjectName(u"cameraIdLabel")

        self.verticalLayout_camera.addWidget(self.cameraIdLabel)

        self.cameraIdSpin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.cameraIdSpin.setObjectName(u"cameraIdSpin")
        self.cameraIdSpin.setMinimum(-2147483648)
        self.cameraIdSpin.setMaximum(2147483647)

        self.verticalLayout_camera.addWidget(self.cameraIdSpin)

        self.cameraAnimLabel = QLabel(self.scrollAreaWidgetContents)
        self.cameraAnimLabel.setObjectName(u"cameraAnimLabel")

        self.verticalLayout_camera.addWidget(self.cameraAnimLabel)

        self.cameraAnimSpin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.cameraAnimSpin.setObjectName(u"cameraAnimSpin")

        self.verticalLayout_camera.addWidget(self.cameraAnimSpin)

        self.cameraAngleLabel = QLabel(self.scrollAreaWidgetContents)
        self.cameraAngleLabel.setObjectName(u"cameraAngleLabel")

        self.verticalLayout_camera.addWidget(self.cameraAngleLabel)

        self.cameraAngleSelect = QComboBox(self.scrollAreaWidgetContents)
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.setObjectName(u"cameraAngleSelect")

        self.verticalLayout_camera.addWidget(self.cameraAngleSelect)

        self.cameraVidEffectLabel = QLabel(self.scrollAreaWidgetContents)
        self.cameraVidEffectLabel.setObjectName(u"cameraVidEffectLabel")

        self.verticalLayout_camera.addWidget(self.cameraVidEffectLabel)

        self.cameraEffectSelect = ComboBox2DA(self.scrollAreaWidgetContents)
        self.cameraEffectSelect.setObjectName(u"cameraEffectSelect")

        self.verticalLayout_camera.addWidget(self.cameraEffectSelect)


        self.verticalLayout_rightDock.addLayout(self.verticalLayout_camera)

        self.verticalLayout_other = QVBoxLayout()
        self.verticalLayout_other.setObjectName(u"verticalLayout_other")
        self.nodeUnskippableCheckbox = QCheckBox(self.scrollAreaWidgetContents)
        self.nodeUnskippableCheckbox.setObjectName(u"nodeUnskippableCheckbox")

        self.verticalLayout_other.addWidget(self.nodeUnskippableCheckbox, 0, Qt.AlignHCenter)

        self.formLayout_other = QFormLayout()
        self.formLayout_other.setObjectName(u"formLayout_other")
        self.formLayout_other.setHorizontalSpacing(2)
        self.formLayout_other.setVerticalSpacing(2)
        self.nodeIdLabel = QLabel(self.scrollAreaWidgetContents)
        self.nodeIdLabel.setObjectName(u"nodeIdLabel")

        self.formLayout_other.setWidget(0, QFormLayout.LabelRole, self.nodeIdLabel)

        self.nodeIdSpin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.nodeIdSpin.setObjectName(u"nodeIdSpin")

        self.formLayout_other.setWidget(0, QFormLayout.FieldRole, self.nodeIdSpin)

        self.alienRaceNodeLabel = QLabel(self.scrollAreaWidgetContents)
        self.alienRaceNodeLabel.setObjectName(u"alienRaceNodeLabel")

        self.formLayout_other.setWidget(1, QFormLayout.LabelRole, self.alienRaceNodeLabel)

        self.alienRaceNodeSpin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.alienRaceNodeSpin.setObjectName(u"alienRaceNodeSpin")

        self.formLayout_other.setWidget(1, QFormLayout.FieldRole, self.alienRaceNodeSpin)

        self.postProcNodeLabel = QLabel(self.scrollAreaWidgetContents)
        self.postProcNodeLabel.setObjectName(u"postProcNodeLabel")

        self.formLayout_other.setWidget(2, QFormLayout.LabelRole, self.postProcNodeLabel)

        self.postProcSpin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.postProcSpin.setObjectName(u"postProcSpin")

        self.formLayout_other.setWidget(2, QFormLayout.FieldRole, self.postProcSpin)

        self.delayNodeLabel = QLabel(self.scrollAreaWidgetContents)
        self.delayNodeLabel.setObjectName(u"delayNodeLabel")

        self.formLayout_other.setWidget(3, QFormLayout.LabelRole, self.delayNodeLabel)

        self.delaySpin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.delaySpin.setObjectName(u"delaySpin")

        self.formLayout_other.setWidget(3, QFormLayout.FieldRole, self.delaySpin)

        self.logicLabel = QLabel(self.scrollAreaWidgetContents)
        self.logicLabel.setObjectName(u"logicLabel")

        self.formLayout_other.setWidget(4, QFormLayout.LabelRole, self.logicLabel)

        self.logicSpin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.logicSpin.setObjectName(u"logicSpin")

        self.formLayout_other.setWidget(4, QFormLayout.FieldRole, self.logicSpin)

        self.waitFlagsLabel = QLabel(self.scrollAreaWidgetContents)
        self.waitFlagsLabel.setObjectName(u"waitFlagsLabel")

        self.formLayout_other.setWidget(5, QFormLayout.LabelRole, self.waitFlagsLabel)

        self.waitFlagSpin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.waitFlagSpin.setObjectName(u"waitFlagSpin")

        self.formLayout_other.setWidget(5, QFormLayout.FieldRole, self.waitFlagSpin)

        self.fadeTypeLabel = QLabel(self.scrollAreaWidgetContents)
        self.fadeTypeLabel.setObjectName(u"fadeTypeLabel")

        self.formLayout_other.setWidget(6, QFormLayout.LabelRole, self.fadeTypeLabel)

        self.fadeTypeSpin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.fadeTypeSpin.setObjectName(u"fadeTypeSpin")

        self.formLayout_other.setWidget(6, QFormLayout.FieldRole, self.fadeTypeSpin)


        self.verticalLayout_other.addLayout(self.formLayout_other)


        self.verticalLayout_rightDock.addLayout(self.verticalLayout_other)

        self.verticalLayout_stunts = QVBoxLayout()
        self.verticalLayout_stunts.setObjectName(u"verticalLayout_stunts")

        self.verticalLayout_rightDock.addLayout(self.verticalLayout_stunts)

        self.scrollArea_rightDock.setWidget(self.scrollAreaWidgetContents)
        self.rightDockWidget.setWidget(self.scrollArea_rightDock)
        MainWindow.addDockWidget(Qt.RightDockWidgetArea, self.rightDockWidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1286, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuTools = QMenu(self.menubar)
        self.menuTools.setObjectName(u"menuTools")
        MainWindow.setMenuBar(self.menubar)
        self.topDockWidget = QDockWidget(MainWindow)
        self.topDockWidget.setObjectName(u"topDockWidget")
        self.topDockWidget.setBaseSize(QSize(845, 151))
        self.topDockWidget.setFocusPolicy(Qt.StrongFocus)
        self.topDockWidgetContents = QWidget()
        self.topDockWidgetContents.setObjectName(u"topDockWidgetContents")
        self.horizontalLayout_13 = QHBoxLayout(self.topDockWidgetContents)
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.horizontalLayout_13.setSizeConstraint(QLayout.SetMinimumSize)
        self.horizontalLayout_13.setContentsMargins(9, 0, 0, 0)
        self.widget = QWidget(self.topDockWidgetContents)
        self.widget.setObjectName(u"widget")
        sizePolicy7 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy7)
        self.widget.setLayoutDirection(Qt.RightToLeft)
        self.gridLayout_4 = QGridLayout(self.widget)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setSizeConstraint(QLayout.SetMinimumSize)
        self.gridLayout_4.setContentsMargins(0, 0, 0, 0)
        self.unequipHandsCheckbox = QCheckBox(self.widget)
        self.unequipHandsCheckbox.setObjectName(u"unequipHandsCheckbox")

        self.gridLayout_4.addWidget(self.unequipHandsCheckbox, 0, 0, 1, 1, Qt.AlignRight|Qt.AlignVCenter)

        self.unequipAllCheckbox = QCheckBox(self.widget)
        self.unequipAllCheckbox.setObjectName(u"unequipAllCheckbox")
        sizePolicy7.setHeightForWidth(self.unequipAllCheckbox.sizePolicy().hasHeightForWidth())
        self.unequipAllCheckbox.setSizePolicy(sizePolicy7)

        self.gridLayout_4.addWidget(self.unequipAllCheckbox, 1, 0, 1, 1, Qt.AlignLeft|Qt.AlignVCenter)

        self.skippableCheckbox = QCheckBox(self.widget)
        self.skippableCheckbox.setObjectName(u"skippableCheckbox")
        sizePolicy7.setHeightForWidth(self.skippableCheckbox.sizePolicy().hasHeightForWidth())
        self.skippableCheckbox.setSizePolicy(sizePolicy7)

        self.gridLayout_4.addWidget(self.skippableCheckbox, 2, 0, 1, 1, Qt.AlignLeft|Qt.AlignVCenter)

        self.animatedCutCheckbox = QCheckBox(self.widget)
        self.animatedCutCheckbox.setObjectName(u"animatedCutCheckbox")
        sizePolicy7.setHeightForWidth(self.animatedCutCheckbox.sizePolicy().hasHeightForWidth())
        self.animatedCutCheckbox.setSizePolicy(sizePolicy7)

        self.gridLayout_4.addWidget(self.animatedCutCheckbox, 3, 0, 1, 1, Qt.AlignLeft|Qt.AlignVCenter)

        self.oldHitCheckbox = QCheckBox(self.widget)
        self.oldHitCheckbox.setObjectName(u"oldHitCheckbox")
        sizePolicy7.setHeightForWidth(self.oldHitCheckbox.sizePolicy().hasHeightForWidth())
        self.oldHitCheckbox.setSizePolicy(sizePolicy7)

        self.gridLayout_4.addWidget(self.oldHitCheckbox, 4, 0, 1, 1, Qt.AlignLeft|Qt.AlignVCenter)


        self.horizontalLayout_13.addWidget(self.widget)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setHorizontalSpacing(5)
        self.gridLayout_3.setVerticalSpacing(3)
        self.gridLayout_3.setContentsMargins(2, -1, 2, -1)
        self.convoTypeLabel = QLabel(self.topDockWidgetContents)
        self.convoTypeLabel.setObjectName(u"convoTypeLabel")

        self.gridLayout_3.addWidget(self.convoTypeLabel, 0, 0, 1, 1)

        self.conversationSelect = QComboBox(self.topDockWidgetContents)
        self.conversationSelect.addItem("")
        self.conversationSelect.addItem("")
        self.conversationSelect.addItem("")
        self.conversationSelect.addItem("")
        self.conversationSelect.addItem("")
        self.conversationSelect.setObjectName(u"conversationSelect")
        sizePolicy8 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy8.setHorizontalStretch(0)
        sizePolicy8.setVerticalStretch(0)
        sizePolicy8.setHeightForWidth(self.conversationSelect.sizePolicy().hasHeightForWidth())
        self.conversationSelect.setSizePolicy(sizePolicy8)

        self.gridLayout_3.addWidget(self.conversationSelect, 0, 1, 1, 1)

        self.computerTypeLabel = QLabel(self.topDockWidgetContents)
        self.computerTypeLabel.setObjectName(u"computerTypeLabel")

        self.gridLayout_3.addWidget(self.computerTypeLabel, 1, 0, 1, 1)

        self.computerSelect = QComboBox(self.topDockWidgetContents)
        self.computerSelect.addItem("")
        self.computerSelect.addItem("")
        self.computerSelect.setObjectName(u"computerSelect")
        sizePolicy8.setHeightForWidth(self.computerSelect.sizePolicy().hasHeightForWidth())
        self.computerSelect.setSizePolicy(sizePolicy8)

        self.gridLayout_3.addWidget(self.computerSelect, 1, 1, 1, 1)

        self.delayReplyLabel = QLabel(self.topDockWidgetContents)
        self.delayReplyLabel.setObjectName(u"delayReplyLabel")

        self.gridLayout_3.addWidget(self.delayReplyLabel, 2, 0, 1, 1)

        self.replyDelaySpin = GFFFieldSpinBox(self.topDockWidgetContents)
        self.replyDelaySpin.setObjectName(u"replyDelaySpin")
        sizePolicy8.setHeightForWidth(self.replyDelaySpin.sizePolicy().hasHeightForWidth())
        self.replyDelaySpin.setSizePolicy(sizePolicy8)
        self.replyDelaySpin.setMinimum(-2147483648)
        self.replyDelaySpin.setMaximum(2147483647)

        self.gridLayout_3.addWidget(self.replyDelaySpin, 2, 1, 1, 1)

        self.delayEntryLabel = QLabel(self.topDockWidgetContents)
        self.delayEntryLabel.setObjectName(u"delayEntryLabel")

        self.gridLayout_3.addWidget(self.delayEntryLabel, 3, 0, 1, 1)

        self.entryDelaySpin = GFFFieldSpinBox(self.topDockWidgetContents)
        self.entryDelaySpin.setObjectName(u"entryDelaySpin")
        sizePolicy8.setHeightForWidth(self.entryDelaySpin.sizePolicy().hasHeightForWidth())
        self.entryDelaySpin.setSizePolicy(sizePolicy8)
        self.entryDelaySpin.setMinimum(-2147483648)
        self.entryDelaySpin.setMaximum(2147483647)

        self.gridLayout_3.addWidget(self.entryDelaySpin, 3, 1, 1, 1)

        self.voiceOverIDLabel = QLabel(self.topDockWidgetContents)
        self.voiceOverIDLabel.setObjectName(u"voiceOverIDLabel")

        self.gridLayout_3.addWidget(self.voiceOverIDLabel, 4, 0, 1, 1)

        self.voIdEdit = QLineEdit(self.topDockWidgetContents)
        self.voIdEdit.setObjectName(u"voIdEdit")
        sizePolicy9 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy9.setHorizontalStretch(0)
        sizePolicy9.setVerticalStretch(0)
        sizePolicy9.setHeightForWidth(self.voIdEdit.sizePolicy().hasHeightForWidth())
        self.voIdEdit.setSizePolicy(sizePolicy9)

        self.gridLayout_3.addWidget(self.voIdEdit, 4, 1, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout_3.addItem(self.verticalSpacer_2, 5, 1, 1, 1)


        self.horizontalLayout_13.addLayout(self.gridLayout_3)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setSizeConstraint(QLayout.SetMinimumSize)
        self.gridLayout_2.setHorizontalSpacing(5)
        self.gridLayout_2.setVerticalSpacing(4)
        self.gridLayout_2.setContentsMargins(2, -1, 2, -1)
        self.ambientTrackCombo = FilterComboBox(self.topDockWidgetContents)
        self.ambientTrackCombo.setObjectName(u"ambientTrackCombo")

        self.gridLayout_2.addWidget(self.ambientTrackCombo, 4, 1, 1, 1)

        self.cameraModelSelect = FilterComboBox(self.topDockWidgetContents)
        self.cameraModelSelect.setObjectName(u"cameraModelSelect")

        self.gridLayout_2.addWidget(self.cameraModelSelect, 2, 1, 1, 1)

        self.onAbortCombo = FilterComboBox(self.topDockWidgetContents)
        self.onAbortCombo.setObjectName(u"onAbortCombo")
        self.onAbortCombo.setMinimumSize(QSize(160, 0))

        self.gridLayout_2.addWidget(self.onAbortCombo, 0, 1, 1, 1)

        self.onEndEdit = FilterComboBox(self.topDockWidgetContents)
        self.onEndEdit.setObjectName(u"onEndEdit")
        self.onEndEdit.setMinimumSize(QSize(160, 0))

        self.gridLayout_2.addWidget(self.onEndEdit, 1, 1, 1, 1)

        self.cameraModelLabel = QLabel(self.topDockWidgetContents)
        self.cameraModelLabel.setObjectName(u"cameraModelLabel")
        sizePolicy10 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sizePolicy10.setHorizontalStretch(0)
        sizePolicy10.setVerticalStretch(0)
        sizePolicy10.setHeightForWidth(self.cameraModelLabel.sizePolicy().hasHeightForWidth())
        self.cameraModelLabel.setSizePolicy(sizePolicy10)

        self.gridLayout_2.addWidget(self.cameraModelLabel, 2, 0, 1, 1, Qt.AlignRight)

        self.convoEndsScriptLabel = QLabel(self.topDockWidgetContents)
        self.convoEndsScriptLabel.setObjectName(u"convoEndsScriptLabel")
        sizePolicy10.setHeightForWidth(self.convoEndsScriptLabel.sizePolicy().hasHeightForWidth())
        self.convoEndsScriptLabel.setSizePolicy(sizePolicy10)

        self.gridLayout_2.addWidget(self.convoEndsScriptLabel, 1, 0, 1, 1, Qt.AlignRight)

        self.convoAbortsScriptLabel = QLabel(self.topDockWidgetContents)
        self.convoAbortsScriptLabel.setObjectName(u"convoAbortsScriptLabel")
        sizePolicy10.setHeightForWidth(self.convoAbortsScriptLabel.sizePolicy().hasHeightForWidth())
        self.convoAbortsScriptLabel.setSizePolicy(sizePolicy10)

        self.gridLayout_2.addWidget(self.convoAbortsScriptLabel, 0, 0, 1, 1, Qt.AlignRight)

        self.ambientTrackLabel = QLabel(self.topDockWidgetContents)
        self.ambientTrackLabel.setObjectName(u"ambientTrackLabel")
        sizePolicy10.setHeightForWidth(self.ambientTrackLabel.sizePolicy().hasHeightForWidth())
        self.ambientTrackLabel.setSizePolicy(sizePolicy10)

        self.gridLayout_2.addWidget(self.ambientTrackLabel, 4, 0, 1, 1, Qt.AlignRight)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout_2.addItem(self.verticalSpacer, 5, 1, 1, 1)


        self.horizontalLayout_13.addLayout(self.gridLayout_2)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SetMinimumSize)
        self.verticalLayout.setContentsMargins(2, -1, 2, -1)
        self.cutsceneModelLabel = QLabel(self.topDockWidgetContents)
        self.cutsceneModelLabel.setObjectName(u"cutsceneModelLabel")

        self.verticalLayout.addWidget(self.cutsceneModelLabel, 0, Qt.AlignHCenter)

        self.stuntList = QListWidget(self.topDockWidgetContents)
        self.stuntList.setObjectName(u"stuntList")

        self.verticalLayout.addWidget(self.stuntList)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setSpacing(0)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalSpacer_10 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_10)

        self.addStuntButton = QPushButton(self.topDockWidgetContents)
        self.addStuntButton.setObjectName(u"addStuntButton")
        sizePolicy11 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy11.setHorizontalStretch(0)
        sizePolicy11.setVerticalStretch(0)
        sizePolicy11.setHeightForWidth(self.addStuntButton.sizePolicy().hasHeightForWidth())
        self.addStuntButton.setSizePolicy(sizePolicy11)
        self.addStuntButton.setBaseSize(QSize(20, 0))

        self.horizontalLayout_5.addWidget(self.addStuntButton)

        self.editStuntButton = QPushButton(self.topDockWidgetContents)
        self.editStuntButton.setObjectName(u"editStuntButton")
        sizePolicy11.setHeightForWidth(self.editStuntButton.sizePolicy().hasHeightForWidth())
        self.editStuntButton.setSizePolicy(sizePolicy11)

        self.horizontalLayout_5.addWidget(self.editStuntButton)

        self.removeStuntButton = QPushButton(self.topDockWidgetContents)
        self.removeStuntButton.setObjectName(u"removeStuntButton")
        sizePolicy11.setHeightForWidth(self.removeStuntButton.sizePolicy().hasHeightForWidth())
        self.removeStuntButton.setSizePolicy(sizePolicy11)

        self.horizontalLayout_5.addWidget(self.removeStuntButton)

        self.horizontalSpacer_11 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_11)


        self.verticalLayout.addLayout(self.horizontalLayout_5)


        self.horizontalLayout_13.addLayout(self.verticalLayout)

        self.horizontalSpacer_12 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer_12)

        self.topDockWidget.setWidget(self.topDockWidgetContents)
        MainWindow.addDockWidget(Qt.TopDockWidgetArea, self.topDockWidget)

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
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"DLGEditor", None))
        self.actionNew.setText(QCoreApplication.translate("MainWindow", u"New", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", u"Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.actionSaveAs.setText(QCoreApplication.translate("MainWindow", u"Save As", None))
        self.actionRevert.setText(QCoreApplication.translate("MainWindow", u"Revert", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.actionReloadTree.setText(QCoreApplication.translate("MainWindow", u"Reload Tree", None))
        self.actionUnfocus.setText(QCoreApplication.translate("MainWindow", u"Unfocus Tree", None))
        self.questEntryLabel.setText(QCoreApplication.translate("MainWindow", u"Quest Entry:", None))
        self.questLabel.setText(QCoreApplication.translate("MainWindow", u"Quest:", None))
        self.listenerTagLabel.setText(QCoreApplication.translate("MainWindow", u"Listener Tag:", None))
        self.speakerEditLabel.setText(QCoreApplication.translate("MainWindow", u"Speaker Tag:", None))
        self.plotXpPercentLabel.setText(QCoreApplication.translate("MainWindow", u"Plot XP Percentage", None))
#if QT_CONFIG(whatsthis)
        self.plotIndexLabel.setWhatsThis(QCoreApplication.translate("MainWindow", u"GFF Field \"PlotIndex\" Int32", None))
#endif // QT_CONFIG(whatsthis)
        self.plotIndexLabel.setText(QCoreApplication.translate("MainWindow", u"Plot Index:", None))
        self.rightDockWidget.setWindowTitle(QCoreApplication.translate("MainWindow", u"Node Fields", None))
        self.commentsEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Comments", None))
        self.script1Label.setText(QCoreApplication.translate("MainWindow", u"Script #1:", None))
        self.script2Label.setText(QCoreApplication.translate("MainWindow", u"Script #2:", None))
        self.conditional1Label.setText(QCoreApplication.translate("MainWindow", u"Conditional #1:", None))
        self.condition1NotCheckbox.setText(QCoreApplication.translate("MainWindow", u"Not", None))
#if QT_CONFIG(tooltip)
        self.condition1Param2Spin.setToolTip(QCoreApplication.translate("MainWindow", u"Param2", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.condition1Param3Spin.setToolTip(QCoreApplication.translate("MainWindow", u"Param3", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.condition1Param4Spin.setToolTip(QCoreApplication.translate("MainWindow", u"Param4", None))
#endif // QT_CONFIG(tooltip)
        self.conditional2Label.setText(QCoreApplication.translate("MainWindow", u"Conditional #2:", None))
        self.condition2NotCheckbox.setText(QCoreApplication.translate("MainWindow", u"Not", None))
        self.curAnimsLabel.setText(QCoreApplication.translate("MainWindow", u"Current Animations", None))
        self.addAnimButton.setText(QCoreApplication.translate("MainWindow", u"Add", None))
        self.removeAnimButton.setText(QCoreApplication.translate("MainWindow", u"Remove", None))
        self.editAnimButton.setText(QCoreApplication.translate("MainWindow", u"Edit", None))
        self.expressionLabel.setText(QCoreApplication.translate("MainWindow", u"Expression:", None))
        self.emotionLabel.setText(QCoreApplication.translate("MainWindow", u"Emotion:", None))
        self.soundLabel.setText(QCoreApplication.translate("MainWindow", u"Sound:", None))
#if QT_CONFIG(tooltip)
        self.soundCheckbox.setToolTip(QCoreApplication.translate("MainWindow", u"'SoundExists' field", None))
#endif // QT_CONFIG(tooltip)
        self.soundCheckbox.setText(QCoreApplication.translate("MainWindow", u"Exists", None))
        self.soundButton.setText(QCoreApplication.translate("MainWindow", u"Play", None))
        self.voiceButton.setText(QCoreApplication.translate("MainWindow", u"Play", None))
        self.voiceLabel.setText(QCoreApplication.translate("MainWindow", u"Voice:", None))
        self.cameraIdLabel.setText(QCoreApplication.translate("MainWindow", u"Camera ID:", None))
        self.cameraAnimLabel.setText(QCoreApplication.translate("MainWindow", u"Camera Animation:", None))
        self.cameraAngleLabel.setText(QCoreApplication.translate("MainWindow", u"Camera Angle:", None))
        self.cameraAngleSelect.setItemText(0, QCoreApplication.translate("MainWindow", u"Auto", None))
        self.cameraAngleSelect.setItemText(1, QCoreApplication.translate("MainWindow", u"Face", None))
        self.cameraAngleSelect.setItemText(2, QCoreApplication.translate("MainWindow", u"Shoulder", None))
        self.cameraAngleSelect.setItemText(3, QCoreApplication.translate("MainWindow", u"Wide Shot", None))
        self.cameraAngleSelect.setItemText(4, QCoreApplication.translate("MainWindow", u"Animated Camera", None))
        self.cameraAngleSelect.setItemText(5, QCoreApplication.translate("MainWindow", u"(DO NOT USE THIS ENTRY)", None))
        self.cameraAngleSelect.setItemText(6, QCoreApplication.translate("MainWindow", u"Static Camera", None))

        self.cameraVidEffectLabel.setText(QCoreApplication.translate("MainWindow", u"Camera Video Effect:", None))
        self.nodeUnskippableCheckbox.setText(QCoreApplication.translate("MainWindow", u"Node Unskippable", None))
        self.nodeIdLabel.setText(QCoreApplication.translate("MainWindow", u"Node ID:", None))
        self.alienRaceNodeLabel.setText(QCoreApplication.translate("MainWindow", u"Alien Race Node:", None))
        self.postProcNodeLabel.setText(QCoreApplication.translate("MainWindow", u"Post Proc Node:", None))
        self.delayNodeLabel.setText(QCoreApplication.translate("MainWindow", u"Delay:", None))
        self.logicLabel.setText(QCoreApplication.translate("MainWindow", u"Logic:", None))
        self.waitFlagsLabel.setText(QCoreApplication.translate("MainWindow", u"Wait Flags:", None))
        self.fadeTypeLabel.setText(QCoreApplication.translate("MainWindow", u"Fade Type:", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuTools.setTitle(QCoreApplication.translate("MainWindow", u"Tools", None))
        self.topDockWidget.setWindowTitle(QCoreApplication.translate("MainWindow", u"File Globals", None))
        self.unequipHandsCheckbox.setText(QCoreApplication.translate("MainWindow", u"Unequip Hands", None))
        self.unequipAllCheckbox.setText(QCoreApplication.translate("MainWindow", u"Unequip All", None))
        self.skippableCheckbox.setText(QCoreApplication.translate("MainWindow", u"Skippable", None))
        self.animatedCutCheckbox.setText(QCoreApplication.translate("MainWindow", u"Animated Cut", None))
        self.oldHitCheckbox.setText(QCoreApplication.translate("MainWindow", u"Old Hit Check", None))
        self.convoTypeLabel.setText(QCoreApplication.translate("MainWindow", u"Conversation Type:", None))
        self.conversationSelect.setItemText(0, QCoreApplication.translate("MainWindow", u"Human", None))
        self.conversationSelect.setItemText(1, QCoreApplication.translate("MainWindow", u"Computer", None))
        self.conversationSelect.setItemText(2, QCoreApplication.translate("MainWindow", u"Type 3", None))
        self.conversationSelect.setItemText(3, QCoreApplication.translate("MainWindow", u"Type 4", None))
        self.conversationSelect.setItemText(4, QCoreApplication.translate("MainWindow", u"Type 5", None))

        self.computerTypeLabel.setText(QCoreApplication.translate("MainWindow", u"Computer Type:", None))
        self.computerSelect.setItemText(0, QCoreApplication.translate("MainWindow", u"Modern", None))
        self.computerSelect.setItemText(1, QCoreApplication.translate("MainWindow", u"Ancient", None))

        self.delayReplyLabel.setText(QCoreApplication.translate("MainWindow", u"Delay before Reply:", None))
        self.delayEntryLabel.setText(QCoreApplication.translate("MainWindow", u"Delay before Entry:", None))
        self.voiceOverIDLabel.setText(QCoreApplication.translate("MainWindow", u"Voiceover ID:", None))
        self.cameraModelLabel.setText(QCoreApplication.translate("MainWindow", u"Camera Model:", None))
        self.convoEndsScriptLabel.setText(QCoreApplication.translate("MainWindow", u"Conversation Ends:", None))
        self.convoAbortsScriptLabel.setText(QCoreApplication.translate("MainWindow", u"Conversation Aborts:", None))
        self.ambientTrackLabel.setText(QCoreApplication.translate("MainWindow", u"Ambient Track:", None))
        self.cutsceneModelLabel.setText(QCoreApplication.translate("MainWindow", u"Cutscene Model", None))
#if QT_CONFIG(tooltip)
        self.stuntList.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Dialogue Stunts list</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.addStuntButton.setText(QCoreApplication.translate("MainWindow", u"Add", None))
        self.editStuntButton.setText(QCoreApplication.translate("MainWindow", u"Edit", None))
        self.removeStuntButton.setText(QCoreApplication.translate("MainWindow", u"Remove", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
