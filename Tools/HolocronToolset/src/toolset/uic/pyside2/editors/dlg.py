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
        MainWindow.resize(866, 773)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QSize(300, 0))
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
        self.dialogTree.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.dialogTree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.dialogTree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dialogTree.setWordWrap(True)
        self.dialogTree.header().setVisible(False)

        self.horizontalLayout_main.addWidget(self.dialogTree)


        self.verticalLayout_main.addLayout(self.horizontalLayout_main)

        self.gridLayout = QGridLayout()
        self.gridLayout.setSpacing(5)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(5, 0, 0, 0)
        self.questEdit = QLineEdit(self.centralwidget)
        self.questEdit.setObjectName(u"questEdit")
        sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.questEdit.sizePolicy().hasHeightForWidth())
        self.questEdit.setSizePolicy(sizePolicy1)
        self.questEdit.setMinimumSize(QSize(150, 0))
        self.questEdit.setMaximumSize(QSize(250, 16777215))

        self.gridLayout.addWidget(self.questEdit, 0, 3, 1, 1)

        self.plotXpSpin = GFFFieldSpinBox(self.centralwidget)
        self.plotXpSpin.setObjectName(u"plotXpSpin")
        sizePolicy1.setHeightForWidth(self.plotXpSpin.sizePolicy().hasHeightForWidth())
        self.plotXpSpin.setSizePolicy(sizePolicy1)
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
        sizePolicy1.setHeightForWidth(self.listenerEdit.sizePolicy().hasHeightForWidth())
        self.listenerEdit.setSizePolicy(sizePolicy1)
        self.listenerEdit.setMinimumSize(QSize(150, 0))
        self.listenerEdit.setMaximumSize(QSize(250, 16777215))

        self.gridLayout.addWidget(self.listenerEdit, 0, 1, 1, 1)

        self.listenerTagLabel = QLabel(self.centralwidget)
        self.listenerTagLabel.setObjectName(u"listenerTagLabel")

        self.gridLayout.addWidget(self.listenerTagLabel, 0, 0, 1, 1, Qt.AlignRight|Qt.AlignVCenter)

        self.speakerEdit = QLineEdit(self.centralwidget)
        self.speakerEdit.setObjectName(u"speakerEdit")
        sizePolicy1.setHeightForWidth(self.speakerEdit.sizePolicy().hasHeightForWidth())
        self.speakerEdit.setSizePolicy(sizePolicy1)
        self.speakerEdit.setMinimumSize(QSize(150, 0))
        self.speakerEdit.setMaximumSize(QSize(250, 16777215))

        self.gridLayout.addWidget(self.speakerEdit, 1, 1, 1, 1)

        self.questEntrySpin = GFFFieldSpinBox(self.centralwidget)
        self.questEntrySpin.setObjectName(u"questEntrySpin")
        self.questEntrySpin.setMinimumSize(QSize(150, 0))
        self.questEntrySpin.setMaximumSize(QSize(250, 16777215))

        self.gridLayout.addWidget(self.questEntrySpin, 1, 3, 1, 1)

        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 1, 0, 1, 1, Qt.AlignRight|Qt.AlignVCenter)

        self.plotXpPercentLabel = QLabel(self.centralwidget)
        self.plotXpPercentLabel.setObjectName(u"plotXpPercentLabel")

        self.gridLayout.addWidget(self.plotXpPercentLabel, 2, 0, 1, 1, Qt.AlignRight)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 1, 4, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_2, 0, 4, 1, 1)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_3, 2, 4, 1, 1)


        self.verticalLayout_main.addLayout(self.gridLayout)

        MainWindow.setCentralWidget(self.centralwidget)
        self.topDockWidget = QDockWidget(MainWindow)
        self.topDockWidget.setObjectName(u"topDockWidget")
        self.topDockWidget.setMinimumSize(QSize(82, 146))
        self.topDockWidgetContents = QWidget()
        self.topDockWidgetContents.setObjectName(u"topDockWidgetContents")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.topDockWidgetContents.sizePolicy().hasHeightForWidth())
        self.topDockWidgetContents.setSizePolicy(sizePolicy2)
        self.layoutWidget = QWidget(self.topDockWidgetContents)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(0, 8, 851, 113))
        self.topGridLayout = QGridLayout(self.layoutWidget)
        self.topGridLayout.setObjectName(u"topGridLayout")
        self.topGridLayout.setContentsMargins(6, 0, 0, 0)
        self.ambientTrackEdit = QLineEdit(self.layoutWidget)
        self.ambientTrackEdit.setObjectName(u"ambientTrackEdit")

        self.topGridLayout.addWidget(self.ambientTrackEdit, 1, 5, 1, 1)

        self.voiceOverIDLabel = QLabel(self.layoutWidget)
        self.voiceOverIDLabel.setObjectName(u"voiceOverIDLabel")
        sizePolicy3 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.voiceOverIDLabel.sizePolicy().hasHeightForWidth())
        self.voiceOverIDLabel.setSizePolicy(sizePolicy3)

        self.topGridLayout.addWidget(self.voiceOverIDLabel, 0, 4, 1, 1, Qt.AlignRight|Qt.AlignVCenter)

        self.computerTypeLabel = QLabel(self.layoutWidget)
        self.computerTypeLabel.setObjectName(u"computerTypeLabel")
        sizePolicy3.setHeightForWidth(self.computerTypeLabel.sizePolicy().hasHeightForWidth())
        self.computerTypeLabel.setSizePolicy(sizePolicy3)

        self.topGridLayout.addWidget(self.computerTypeLabel, 3, 0, 1, 1, Qt.AlignHCenter|Qt.AlignVCenter)

        self.conversationSelect = QComboBox(self.layoutWidget)
        self.conversationSelect.addItem("")
        self.conversationSelect.addItem("")
        self.conversationSelect.addItem("")
        self.conversationSelect.addItem("")
        self.conversationSelect.addItem("")
        self.conversationSelect.setObjectName(u"conversationSelect")
        self.conversationSelect.setMinimumSize(QSize(160, 0))

        self.topGridLayout.addWidget(self.conversationSelect, 2, 1, 1, 1)

        self.computerSelect = QComboBox(self.layoutWidget)
        self.computerSelect.addItem("")
        self.computerSelect.addItem("")
        self.computerSelect.setObjectName(u"computerSelect")
        self.computerSelect.setMinimumSize(QSize(160, 0))

        self.topGridLayout.addWidget(self.computerSelect, 3, 1, 1, 1)

        self.onAbortEdit = FilterComboBox(self.layoutWidget)
        self.onAbortEdit.setObjectName(u"onAbortEdit")
        self.onAbortEdit.setMinimumSize(QSize(160, 0))

        self.topGridLayout.addWidget(self.onAbortEdit, 1, 1, 1, 1)

        self.convoEndsScriptLabel = QLabel(self.layoutWidget)
        self.convoEndsScriptLabel.setObjectName(u"convoEndsScriptLabel")
        sizePolicy3.setHeightForWidth(self.convoEndsScriptLabel.sizePolicy().hasHeightForWidth())
        self.convoEndsScriptLabel.setSizePolicy(sizePolicy3)

        self.topGridLayout.addWidget(self.convoEndsScriptLabel, 0, 0, 1, 1, Qt.AlignRight|Qt.AlignVCenter)

        self.convoTypeLabel = QLabel(self.layoutWidget)
        self.convoTypeLabel.setObjectName(u"convoTypeLabel")
        sizePolicy3.setHeightForWidth(self.convoTypeLabel.sizePolicy().hasHeightForWidth())
        self.convoTypeLabel.setSizePolicy(sizePolicy3)

        self.topGridLayout.addWidget(self.convoTypeLabel, 2, 0, 1, 1, Qt.AlignHCenter|Qt.AlignVCenter)

        self.ambientTrackLabel = QLabel(self.layoutWidget)
        self.ambientTrackLabel.setObjectName(u"ambientTrackLabel")

        self.topGridLayout.addWidget(self.ambientTrackLabel, 1, 4, 1, 1, Qt.AlignRight|Qt.AlignVCenter)

        self.convoAbortsScriptLabel = QLabel(self.layoutWidget)
        self.convoAbortsScriptLabel.setObjectName(u"convoAbortsScriptLabel")
        sizePolicy.setHeightForWidth(self.convoAbortsScriptLabel.sizePolicy().hasHeightForWidth())
        self.convoAbortsScriptLabel.setSizePolicy(sizePolicy)

        self.topGridLayout.addWidget(self.convoAbortsScriptLabel, 1, 0, 1, 1, Qt.AlignVCenter)

        self.voIdEdit = QLineEdit(self.layoutWidget)
        self.voIdEdit.setObjectName(u"voIdEdit")

        self.topGridLayout.addWidget(self.voIdEdit, 0, 5, 1, 1)

        self.onEndEdit = FilterComboBox(self.layoutWidget)
        self.onEndEdit.setObjectName(u"onEndEdit")
        self.onEndEdit.setMinimumSize(QSize(160, 0))
        self.onEndEdit.setMaximumSize(QSize(160, 16777215))

        self.topGridLayout.addWidget(self.onEndEdit, 0, 1, 1, 1)

        self.delayEntryLabel = QLabel(self.layoutWidget)
        self.delayEntryLabel.setObjectName(u"delayEntryLabel")

        self.topGridLayout.addWidget(self.delayEntryLabel, 0, 2, 1, 1, Qt.AlignRight|Qt.AlignVCenter)

        self.replyDelaySpin = GFFFieldSpinBox(self.layoutWidget)
        self.replyDelaySpin.setObjectName(u"replyDelaySpin")
        sizePolicy.setHeightForWidth(self.replyDelaySpin.sizePolicy().hasHeightForWidth())
        self.replyDelaySpin.setSizePolicy(sizePolicy)
        self.replyDelaySpin.setMinimum(-2147483648)
        self.replyDelaySpin.setMaximum(2147483647)

        self.topGridLayout.addWidget(self.replyDelaySpin, 0, 3, 1, 1)

        self.delayReplyLabel = QLabel(self.layoutWidget)
        self.delayReplyLabel.setObjectName(u"delayReplyLabel")

        self.topGridLayout.addWidget(self.delayReplyLabel, 1, 2, 1, 1, Qt.AlignRight|Qt.AlignVCenter)

        self.entryDelaySpin = GFFFieldSpinBox(self.layoutWidget)
        self.entryDelaySpin.setObjectName(u"entryDelaySpin")
        sizePolicy.setHeightForWidth(self.entryDelaySpin.sizePolicy().hasHeightForWidth())
        self.entryDelaySpin.setSizePolicy(sizePolicy)
        self.entryDelaySpin.setMinimum(-2147483648)
        self.entryDelaySpin.setMaximum(2147483647)

        self.topGridLayout.addWidget(self.entryDelaySpin, 1, 3, 1, 1)

        self.skippableCheckbox = QCheckBox(self.layoutWidget)
        self.skippableCheckbox.setObjectName(u"skippableCheckbox")
        sizePolicy.setHeightForWidth(self.skippableCheckbox.sizePolicy().hasHeightForWidth())
        self.skippableCheckbox.setSizePolicy(sizePolicy)

        self.topGridLayout.addWidget(self.skippableCheckbox, 2, 2, 1, 1, Qt.AlignLeft)

        self.unequipHandsCheckbox = QCheckBox(self.layoutWidget)
        self.unequipHandsCheckbox.setObjectName(u"unequipHandsCheckbox")

        self.topGridLayout.addWidget(self.unequipHandsCheckbox, 3, 2, 1, 1, Qt.AlignLeft)

        self.unequipAllCheckbox = QCheckBox(self.layoutWidget)
        self.unequipAllCheckbox.setObjectName(u"unequipAllCheckbox")
        sizePolicy.setHeightForWidth(self.unequipAllCheckbox.sizePolicy().hasHeightForWidth())
        self.unequipAllCheckbox.setSizePolicy(sizePolicy)

        self.topGridLayout.addWidget(self.unequipAllCheckbox, 3, 3, 1, 1, Qt.AlignLeft)

        self.animatedCutCheckbox = QCheckBox(self.layoutWidget)
        self.animatedCutCheckbox.setObjectName(u"animatedCutCheckbox")
        sizePolicy.setHeightForWidth(self.animatedCutCheckbox.sizePolicy().hasHeightForWidth())
        self.animatedCutCheckbox.setSizePolicy(sizePolicy)

        self.topGridLayout.addWidget(self.animatedCutCheckbox, 2, 3, 1, 1, Qt.AlignLeft)

        self.cameraModelLabel = QLabel(self.layoutWidget)
        self.cameraModelLabel.setObjectName(u"cameraModelLabel")
        sizePolicy3.setHeightForWidth(self.cameraModelLabel.sizePolicy().hasHeightForWidth())
        self.cameraModelLabel.setSizePolicy(sizePolicy3)

        self.topGridLayout.addWidget(self.cameraModelLabel, 2, 4, 1, 1, Qt.AlignRight|Qt.AlignVCenter)

        self.cameraModelEdit = QLineEdit(self.layoutWidget)
        self.cameraModelEdit.setObjectName(u"cameraModelEdit")

        self.topGridLayout.addWidget(self.cameraModelEdit, 2, 5, 1, 1)

        self.oldHitCheckbox = QCheckBox(self.layoutWidget)
        self.oldHitCheckbox.setObjectName(u"oldHitCheckbox")

        self.topGridLayout.addWidget(self.oldHitCheckbox, 3, 5, 1, 1, Qt.AlignLeft)

        self.topDockWidget.setWidget(self.topDockWidgetContents)
        MainWindow.addDockWidget(Qt.TopDockWidgetArea, self.topDockWidget)
        self.rightDockWidget = QDockWidget(MainWindow)
        self.rightDockWidget.setObjectName(u"rightDockWidget")
        self.rightDockWidget.setMinimumSize(QSize(310, 100))
        self.rightDockWidget.setFloating(True)
        self.rightDockWidget.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.scrollArea_rightDock = QScrollArea()
        self.scrollArea_rightDock.setObjectName(u"scrollArea_rightDock")
        self.scrollArea_rightDock.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 291, 1141))
        self.verticalLayout_rightDock = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_rightDock.setSpacing(0)
        self.verticalLayout_rightDock.setObjectName(u"verticalLayout_rightDock")
        self.verticalLayout_rightDock.setContentsMargins(2, 0, 2, 0)
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
        sizePolicy3.setHeightForWidth(self.script1Label.sizePolicy().hasHeightForWidth())
        self.script1Label.setSizePolicy(sizePolicy3)
        self.script1Label.setMinimumSize(QSize(80, 0))
        self.script1Label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout.addWidget(self.script1Label, 0, Qt.AlignRight|Qt.AlignVCenter)

        self.script1ResrefEdit = FilterComboBox(self.scrollAreaWidgetContents)
        self.script1ResrefEdit.setObjectName(u"script1ResrefEdit")
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
        sizePolicy.setHeightForWidth(self.script1Param1Spin.sizePolicy().hasHeightForWidth())
        self.script1Param1Spin.setSizePolicy(sizePolicy)
        self.script1Param1Spin.setMinimumSize(QSize(30, 0))
        self.script1Param1Spin.setMinimum(-2147483648)
        self.script1Param1Spin.setMaximum(2147483647)

        self.horizontalLayout_script1Params.addWidget(self.script1Param1Spin)

        self.script1Param2Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script1Param2Spin.setObjectName(u"script1Param2Spin")
        sizePolicy.setHeightForWidth(self.script1Param2Spin.sizePolicy().hasHeightForWidth())
        self.script1Param2Spin.setSizePolicy(sizePolicy)
        self.script1Param2Spin.setMinimumSize(QSize(30, 0))
        self.script1Param2Spin.setMinimum(-2147483648)
        self.script1Param2Spin.setMaximum(2147483647)

        self.horizontalLayout_script1Params.addWidget(self.script1Param2Spin)

        self.script1Param3Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script1Param3Spin.setObjectName(u"script1Param3Spin")
        sizePolicy.setHeightForWidth(self.script1Param3Spin.sizePolicy().hasHeightForWidth())
        self.script1Param3Spin.setSizePolicy(sizePolicy)
        self.script1Param3Spin.setMinimumSize(QSize(30, 0))
        self.script1Param3Spin.setMinimum(-2147483648)
        self.script1Param3Spin.setMaximum(2147483647)

        self.horizontalLayout_script1Params.addWidget(self.script1Param3Spin)

        self.script1Param4Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script1Param4Spin.setObjectName(u"script1Param4Spin")
        sizePolicy.setHeightForWidth(self.script1Param4Spin.sizePolicy().hasHeightForWidth())
        self.script1Param4Spin.setSizePolicy(sizePolicy)
        self.script1Param4Spin.setMinimumSize(QSize(30, 0))
        self.script1Param4Spin.setMinimum(-2147483648)
        self.script1Param4Spin.setMaximum(2147483647)

        self.horizontalLayout_script1Params.addWidget(self.script1Param4Spin)

        self.script1Param5Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script1Param5Spin.setObjectName(u"script1Param5Spin")
        sizePolicy.setHeightForWidth(self.script1Param5Spin.sizePolicy().hasHeightForWidth())
        self.script1Param5Spin.setSizePolicy(sizePolicy)
        self.script1Param5Spin.setMinimumSize(QSize(30, 0))

        self.horizontalLayout_script1Params.addWidget(self.script1Param5Spin)

        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_script1Params.addItem(self.horizontalSpacer_9)

        self.script1Param6Edit = QLineEdit(self.scrollAreaWidgetContents)
        self.script1Param6Edit.setObjectName(u"script1Param6Edit")
        self.script1Param6Edit.setMinimumSize(QSize(0, 0))

        self.horizontalLayout_script1Params.addWidget(self.script1Param6Edit)


        self.verticalLayout_scripts.addLayout(self.horizontalLayout_script1Params)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.script2Label = QLabel(self.scrollAreaWidgetContents)
        self.script2Label.setObjectName(u"script2Label")
        sizePolicy3.setHeightForWidth(self.script2Label.sizePolicy().hasHeightForWidth())
        self.script2Label.setSizePolicy(sizePolicy3)
        self.script2Label.setMinimumSize(QSize(80, 0))
        self.script2Label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_2.addWidget(self.script2Label, 0, Qt.AlignRight|Qt.AlignVCenter)

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
        sizePolicy.setHeightForWidth(self.script2Param1Spin.sizePolicy().hasHeightForWidth())
        self.script2Param1Spin.setSizePolicy(sizePolicy)
        self.script2Param1Spin.setMinimumSize(QSize(30, 0))
        self.script2Param1Spin.setMinimum(-2147483648)
        self.script2Param1Spin.setMaximum(2147483647)

        self.horizontalLayout_script2Params.addWidget(self.script2Param1Spin)

        self.script2Param2Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script2Param2Spin.setObjectName(u"script2Param2Spin")
        sizePolicy.setHeightForWidth(self.script2Param2Spin.sizePolicy().hasHeightForWidth())
        self.script2Param2Spin.setSizePolicy(sizePolicy)
        self.script2Param2Spin.setMinimumSize(QSize(30, 0))
        self.script2Param2Spin.setMinimum(-2147483648)
        self.script2Param2Spin.setMaximum(2147483647)

        self.horizontalLayout_script2Params.addWidget(self.script2Param2Spin)

        self.script2Param3Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script2Param3Spin.setObjectName(u"script2Param3Spin")
        sizePolicy.setHeightForWidth(self.script2Param3Spin.sizePolicy().hasHeightForWidth())
        self.script2Param3Spin.setSizePolicy(sizePolicy)
        self.script2Param3Spin.setMinimumSize(QSize(30, 0))
        self.script2Param3Spin.setMinimum(-2147483648)
        self.script2Param3Spin.setMaximum(2147483647)

        self.horizontalLayout_script2Params.addWidget(self.script2Param3Spin)

        self.script2Param4Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script2Param4Spin.setObjectName(u"script2Param4Spin")
        sizePolicy.setHeightForWidth(self.script2Param4Spin.sizePolicy().hasHeightForWidth())
        self.script2Param4Spin.setSizePolicy(sizePolicy)
        self.script2Param4Spin.setMinimumSize(QSize(30, 0))
        self.script2Param4Spin.setMinimum(-2147483648)
        self.script2Param4Spin.setMaximum(2147483647)

        self.horizontalLayout_script2Params.addWidget(self.script2Param4Spin)

        self.script2Param5Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script2Param5Spin.setObjectName(u"script2Param5Spin")
        sizePolicy.setHeightForWidth(self.script2Param5Spin.sizePolicy().hasHeightForWidth())
        self.script2Param5Spin.setSizePolicy(sizePolicy)
        self.script2Param5Spin.setMinimumSize(QSize(30, 0))
        self.script2Param5Spin.setMinimum(-2147483648)
        self.script2Param5Spin.setMaximum(2147483647)

        self.horizontalLayout_script2Params.addWidget(self.script2Param5Spin)

        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_script2Params.addItem(self.horizontalSpacer_8)

        self.script2Param6Edit = QLineEdit(self.scrollAreaWidgetContents)
        self.script2Param6Edit.setObjectName(u"script2Param6Edit")

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
        sizePolicy3.setHeightForWidth(self.conditional1Label.sizePolicy().hasHeightForWidth())
        self.conditional1Label.setSizePolicy(sizePolicy3)
        self.conditional1Label.setMinimumSize(QSize(80, 0))

        self.horizontalLayout_3.addWidget(self.conditional1Label, 0, Qt.AlignVCenter)

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
        sizePolicy.setHeightForWidth(self.condition1Param1Spin.sizePolicy().hasHeightForWidth())
        self.condition1Param1Spin.setSizePolicy(sizePolicy)
        self.condition1Param1Spin.setMinimumSize(QSize(30, 0))
        self.condition1Param1Spin.setMinimum(-2147483648)
        self.condition1Param1Spin.setMaximum(2147483647)

        self.horizontalLayout_condition1Params.addWidget(self.condition1Param1Spin)

        self.condition1Param2Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition1Param2Spin.setObjectName(u"condition1Param2Spin")
        sizePolicy.setHeightForWidth(self.condition1Param2Spin.sizePolicy().hasHeightForWidth())
        self.condition1Param2Spin.setSizePolicy(sizePolicy)
        self.condition1Param2Spin.setMinimumSize(QSize(30, 0))
        self.condition1Param2Spin.setMinimum(-2147483648)
        self.condition1Param2Spin.setMaximum(2147483647)

        self.horizontalLayout_condition1Params.addWidget(self.condition1Param2Spin)

        self.condition1Param3Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition1Param3Spin.setObjectName(u"condition1Param3Spin")
        sizePolicy.setHeightForWidth(self.condition1Param3Spin.sizePolicy().hasHeightForWidth())
        self.condition1Param3Spin.setSizePolicy(sizePolicy)
        self.condition1Param3Spin.setMinimumSize(QSize(30, 0))
        self.condition1Param3Spin.setMinimum(-2147483648)
        self.condition1Param3Spin.setMaximum(2147483647)

        self.horizontalLayout_condition1Params.addWidget(self.condition1Param3Spin)

        self.condition1Param4Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition1Param4Spin.setObjectName(u"condition1Param4Spin")
        sizePolicy.setHeightForWidth(self.condition1Param4Spin.sizePolicy().hasHeightForWidth())
        self.condition1Param4Spin.setSizePolicy(sizePolicy)
        self.condition1Param4Spin.setMinimumSize(QSize(30, 0))
        self.condition1Param4Spin.setMinimum(-2147483648)
        self.condition1Param4Spin.setMaximum(2147483647)

        self.horizontalLayout_condition1Params.addWidget(self.condition1Param4Spin)

        self.condition1Param5Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition1Param5Spin.setObjectName(u"condition1Param5Spin")
        sizePolicy.setHeightForWidth(self.condition1Param5Spin.sizePolicy().hasHeightForWidth())
        self.condition1Param5Spin.setSizePolicy(sizePolicy)
        self.condition1Param5Spin.setMinimumSize(QSize(30, 0))
        self.condition1Param5Spin.setMinimum(-2147483648)
        self.condition1Param5Spin.setMaximum(2147483647)

        self.horizontalLayout_condition1Params.addWidget(self.condition1Param5Spin)

        self.condition1Param6Edit = QLineEdit(self.scrollAreaWidgetContents)
        self.condition1Param6Edit.setObjectName(u"condition1Param6Edit")

        self.horizontalLayout_condition1Params.addWidget(self.condition1Param6Edit)


        self.verticalLayout_conditions.addLayout(self.horizontalLayout_condition1Params)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(2)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.conditional2Label = QLabel(self.scrollAreaWidgetContents)
        self.conditional2Label.setObjectName(u"conditional2Label")
        sizePolicy3.setHeightForWidth(self.conditional2Label.sizePolicy().hasHeightForWidth())
        self.conditional2Label.setSizePolicy(sizePolicy3)
        self.conditional2Label.setMinimumSize(QSize(80, 0))

        self.horizontalLayout_4.addWidget(self.conditional2Label, 0, Qt.AlignVCenter)

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
        sizePolicy.setHeightForWidth(self.condition2Param1Spin.sizePolicy().hasHeightForWidth())
        self.condition2Param1Spin.setSizePolicy(sizePolicy)
        self.condition2Param1Spin.setMinimumSize(QSize(30, 0))
        self.condition2Param1Spin.setMinimum(-2147483648)
        self.condition2Param1Spin.setMaximum(2147483647)

        self.horizontalLayout_condition2Params.addWidget(self.condition2Param1Spin)

        self.condition2Param2Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition2Param2Spin.setObjectName(u"condition2Param2Spin")
        sizePolicy.setHeightForWidth(self.condition2Param2Spin.sizePolicy().hasHeightForWidth())
        self.condition2Param2Spin.setSizePolicy(sizePolicy)
        self.condition2Param2Spin.setMinimumSize(QSize(30, 0))
        self.condition2Param2Spin.setMinimum(-2147483648)
        self.condition2Param2Spin.setMaximum(2147483647)

        self.horizontalLayout_condition2Params.addWidget(self.condition2Param2Spin)

        self.condition2Param3Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition2Param3Spin.setObjectName(u"condition2Param3Spin")
        sizePolicy.setHeightForWidth(self.condition2Param3Spin.sizePolicy().hasHeightForWidth())
        self.condition2Param3Spin.setSizePolicy(sizePolicy)
        self.condition2Param3Spin.setMinimumSize(QSize(30, 0))
        self.condition2Param3Spin.setMinimum(-2147483648)
        self.condition2Param3Spin.setMaximum(2147483647)

        self.horizontalLayout_condition2Params.addWidget(self.condition2Param3Spin)

        self.condition2Param4Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition2Param4Spin.setObjectName(u"condition2Param4Spin")
        sizePolicy.setHeightForWidth(self.condition2Param4Spin.sizePolicy().hasHeightForWidth())
        self.condition2Param4Spin.setSizePolicy(sizePolicy)
        self.condition2Param4Spin.setMinimumSize(QSize(30, 0))
        self.condition2Param4Spin.setMinimum(-2147483648)
        self.condition2Param4Spin.setMaximum(2147483647)

        self.horizontalLayout_condition2Params.addWidget(self.condition2Param4Spin)

        self.condition2Param5Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition2Param5Spin.setObjectName(u"condition2Param5Spin")
        sizePolicy.setHeightForWidth(self.condition2Param5Spin.sizePolicy().hasHeightForWidth())
        self.condition2Param5Spin.setSizePolicy(sizePolicy)
        self.condition2Param5Spin.setMinimumSize(QSize(30, 0))
        self.condition2Param5Spin.setMinimum(-2147483648)
        self.condition2Param5Spin.setMaximum(2147483647)

        self.horizontalLayout_condition2Params.addWidget(self.condition2Param5Spin)

        self.condition2Param6Edit = QLineEdit(self.scrollAreaWidgetContents)
        self.condition2Param6Edit.setObjectName(u"condition2Param6Edit")

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
        sizePolicy.setHeightForWidth(self.soundLabel.sizePolicy().hasHeightForWidth())
        self.soundLabel.setSizePolicy(sizePolicy)

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
        self.plotIndexLabel = QLabel(self.scrollAreaWidgetContents)
        self.plotIndexLabel.setObjectName(u"plotIndexLabel")

        self.verticalLayout_journal.addWidget(self.plotIndexLabel)

        self.plotIndexSpin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.plotIndexSpin.setObjectName(u"plotIndexSpin")
        self.plotIndexSpin.setMinimum(-2147483648)
        self.plotIndexSpin.setMaximum(2147483647)

        self.verticalLayout_journal.addWidget(self.plotIndexSpin)


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

        self.verticalLayout_other.addWidget(self.nodeUnskippableCheckbox)

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
        self.cutsceneModelLabel = QLabel(self.scrollAreaWidgetContents)
        self.cutsceneModelLabel.setObjectName(u"cutsceneModelLabel")

        self.verticalLayout_stunts.addWidget(self.cutsceneModelLabel)

        self.stuntList = QListWidget(self.scrollAreaWidgetContents)
        self.stuntList.setObjectName(u"stuntList")

        self.verticalLayout_stunts.addWidget(self.stuntList)

        self.horizontalLayout_stuntButtons = QHBoxLayout()
        self.horizontalLayout_stuntButtons.setObjectName(u"horizontalLayout_stuntButtons")
        self.addStuntButton = QPushButton(self.scrollAreaWidgetContents)
        self.addStuntButton.setObjectName(u"addStuntButton")

        self.horizontalLayout_stuntButtons.addWidget(self.addStuntButton)

        self.removeStuntButton = QPushButton(self.scrollAreaWidgetContents)
        self.removeStuntButton.setObjectName(u"removeStuntButton")

        self.horizontalLayout_stuntButtons.addWidget(self.removeStuntButton)

        self.editStuntButton = QPushButton(self.scrollAreaWidgetContents)
        self.editStuntButton.setObjectName(u"editStuntButton")

        self.horizontalLayout_stuntButtons.addWidget(self.editStuntButton)


        self.verticalLayout_stunts.addLayout(self.horizontalLayout_stuntButtons)


        self.verticalLayout_rightDock.addLayout(self.verticalLayout_stunts)

        self.scrollArea_rightDock.setWidget(self.scrollAreaWidgetContents)
        self.rightDockWidget.setWidget(self.scrollArea_rightDock)
        MainWindow.addDockWidget(Qt.RightDockWidgetArea, self.rightDockWidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 866, 22))
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
        self.questEntryLabel.setText(QCoreApplication.translate("MainWindow", u"Quest Entry:", None))
        self.questLabel.setText(QCoreApplication.translate("MainWindow", u"Quest:", None))
        self.listenerTagLabel.setText(QCoreApplication.translate("MainWindow", u"Listener Tag:", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Speaker Tag:", None))
        self.plotXpPercentLabel.setText(QCoreApplication.translate("MainWindow", u"Plot XP (percent)", None))
        self.topDockWidget.setWindowTitle(QCoreApplication.translate("MainWindow", u"File Globals", None))
        self.voiceOverIDLabel.setText(QCoreApplication.translate("MainWindow", u"Voiceover ID:", None))
        self.computerTypeLabel.setText(QCoreApplication.translate("MainWindow", u"Computer Type:", None))
        self.conversationSelect.setItemText(0, QCoreApplication.translate("MainWindow", u"Human", None))
        self.conversationSelect.setItemText(1, QCoreApplication.translate("MainWindow", u"Computer", None))
        self.conversationSelect.setItemText(2, QCoreApplication.translate("MainWindow", u"Type 3", None))
        self.conversationSelect.setItemText(3, QCoreApplication.translate("MainWindow", u"Type 4", None))
        self.conversationSelect.setItemText(4, QCoreApplication.translate("MainWindow", u"Type 5", None))

        self.computerSelect.setItemText(0, QCoreApplication.translate("MainWindow", u"Modern", None))
        self.computerSelect.setItemText(1, QCoreApplication.translate("MainWindow", u"Ancient", None))

        self.convoEndsScriptLabel.setText(QCoreApplication.translate("MainWindow", u"Conversation Ends Script:", None))
        self.convoTypeLabel.setText(QCoreApplication.translate("MainWindow", u"Conversation Type:", None))
        self.ambientTrackLabel.setText(QCoreApplication.translate("MainWindow", u"Ambient Track:", None))
        self.convoAbortsScriptLabel.setText(QCoreApplication.translate("MainWindow", u"Conversation Aborts Script:", None))
        self.delayEntryLabel.setText(QCoreApplication.translate("MainWindow", u"Delay before entry:", None))
        self.delayReplyLabel.setText(QCoreApplication.translate("MainWindow", u"Delay before reply:", None))
        self.skippableCheckbox.setText(QCoreApplication.translate("MainWindow", u"Skippable", None))
        self.unequipHandsCheckbox.setText(QCoreApplication.translate("MainWindow", u"Unequip Hands", None))
        self.unequipAllCheckbox.setText(QCoreApplication.translate("MainWindow", u"Unequip All", None))
        self.animatedCutCheckbox.setText(QCoreApplication.translate("MainWindow", u"Animated Cut", None))
        self.cameraModelLabel.setText(QCoreApplication.translate("MainWindow", u"Camera Model:", None))
        self.oldHitCheckbox.setText(QCoreApplication.translate("MainWindow", u"Old Hit Check", None))
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
        self.plotIndexLabel.setText(QCoreApplication.translate("MainWindow", u"Plot Index:", None))
        self.cameraIdLabel.setText(QCoreApplication.translate("MainWindow", u"Camera ID:", None))
        self.cameraAnimLabel.setText(QCoreApplication.translate("MainWindow", u"Camera Animation:", None))
        self.cameraAngleLabel.setText(QCoreApplication.translate("MainWindow", u"Camera Angle:", None))
        self.cameraAngleSelect.setItemText(0, QCoreApplication.translate("MainWindow", u"Auto", None))
        self.cameraAngleSelect.setItemText(1, QCoreApplication.translate("MainWindow", u"Face", None))
        self.cameraAngleSelect.setItemText(2, QCoreApplication.translate("MainWindow", u"Shoulder", None))
        self.cameraAngleSelect.setItemText(3, QCoreApplication.translate("MainWindow", u"Wide Shot", None))
        self.cameraAngleSelect.setItemText(4, QCoreApplication.translate("MainWindow", u"Animated Camera", None))
        self.cameraAngleSelect.setItemText(5, QCoreApplication.translate("MainWindow", u"No Change", None))
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
        self.cutsceneModelLabel.setText(QCoreApplication.translate("MainWindow", u"Cutscene Model:", None))
#if QT_CONFIG(tooltip)
        self.stuntList.setToolTip(QCoreApplication.translate("MainWindow", u"Stunt List", None))
#endif // QT_CONFIG(tooltip)
        self.addStuntButton.setText(QCoreApplication.translate("MainWindow", u"Add", None))
        self.removeStuntButton.setText(QCoreApplication.translate("MainWindow", u"Remove", None))
        self.editStuntButton.setText(QCoreApplication.translate("MainWindow", u"Edit", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuTools.setTitle(QCoreApplication.translate("MainWindow", u"Tools", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
