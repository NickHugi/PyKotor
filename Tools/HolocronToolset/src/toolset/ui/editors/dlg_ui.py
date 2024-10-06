
################################################################################
## Form generated from reading UI file 'dlg.ui'
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
    QDockWidget,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QListWidget,
    QMenu,
    QMenuBar,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from toolset.gui.editors.dlg import DLGTreeView
from toolset.gui.widgets.edit.combobox_2da import ComboBox2DA
from toolset.gui.widgets.edit.spinbox import GFFFieldSpinBox
from utility.ui_libraries.qt.widgets.widgets.combobox import FilterComboBox


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(944, 819)
        MainWindow.setMouseTracking(True)
        MainWindow.setDockNestingEnabled(True)
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
        self.centralwidget.setMouseTracking(True)
        self.verticalLayout_main = QVBoxLayout(self.centralwidget)
        self.verticalLayout_main.setSpacing(6)
        self.verticalLayout_main.setObjectName("verticalLayout_main")
        self.verticalLayout_main.setContentsMargins(2, 2, 2, 2)
        self.horizontalLayout_main = QHBoxLayout()
        self.horizontalLayout_main.setSpacing(0)
        self.horizontalLayout_main.setObjectName("horizontalLayout_main")
        self.dialogTree = DLGTreeView(self.centralwidget)
        self.dialogTree.setObjectName("dialogTree")
        self.dialogTree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.dialogTree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dialogTree.setExpandsOnDoubleClick(False)

        self.horizontalLayout_main.addWidget(self.dialogTree)


        self.verticalLayout_main.addLayout(self.horizontalLayout_main)

        MainWindow.setCentralWidget(self.centralwidget)
        self.rightDockWidget = QDockWidget(MainWindow)
        self.rightDockWidget.setObjectName("rightDockWidget")
        self.rightDockWidget.setMinimumSize(QSize(310, 100))
        self.rightDockWidget.setBaseSize(QSize(310, 100))
        self.rightDockWidget.setFloating(False)
        self.rightDockWidget.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.scrollArea_rightDock = QScrollArea()
        self.scrollArea_rightDock.setObjectName("scrollArea_rightDock")
        self.scrollArea_rightDock.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 302, 903))
        self.verticalLayout_rightDock = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_rightDock.setSpacing(0)
        self.verticalLayout_rightDock.setObjectName("verticalLayout_rightDock")
        self.verticalLayout_rightDock.setContentsMargins(0, 0, 2, 0)
        self.verticalLayout_scripts = QVBoxLayout()
        self.verticalLayout_scripts.setSpacing(0)
        self.verticalLayout_scripts.setObjectName("verticalLayout_scripts")
        self.verticalLayout_scripts.setContentsMargins(0, 0, 0, 0)
        self.commentsEdit = QPlainTextEdit(self.scrollAreaWidgetContents)
        self.commentsEdit.setObjectName("commentsEdit")

        self.verticalLayout_scripts.addWidget(self.commentsEdit)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.script1Label = QLabel(self.scrollAreaWidgetContents)
        self.script1Label.setObjectName("script1Label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.script1Label.sizePolicy().hasHeightForWidth())
        self.script1Label.setSizePolicy(sizePolicy)
        self.script1Label.setMinimumSize(QSize(100, 0))
        self.script1Label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout.addWidget(self.script1Label, 0, Qt.AlignLeft)

        self.script1ResrefEdit = FilterComboBox(self.scrollAreaWidgetContents)
        self.script1ResrefEdit.setObjectName("script1ResrefEdit")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.script1ResrefEdit.sizePolicy().hasHeightForWidth())
        self.script1ResrefEdit.setSizePolicy(sizePolicy1)
        self.script1ResrefEdit.setMinimumSize(QSize(150, 0))
        self.script1ResrefEdit.setMaximumSize(QSize(16777215, 16777215))

        self.horizontalLayout.addWidget(self.script1ResrefEdit)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_4)


        self.verticalLayout_scripts.addLayout(self.horizontalLayout)

        self.horizontalLayout_script1Params = QHBoxLayout()
        self.horizontalLayout_script1Params.setSpacing(0)
        self.horizontalLayout_script1Params.setObjectName("horizontalLayout_script1Params")
        self.script1Param1Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script1Param1Spin.setObjectName("script1Param1Spin")
        sizePolicy1.setHeightForWidth(self.script1Param1Spin.sizePolicy().hasHeightForWidth())
        self.script1Param1Spin.setSizePolicy(sizePolicy1)
        self.script1Param1Spin.setMinimumSize(QSize(30, 0))
        self.script1Param1Spin.setMinimum(-2147483648)
        self.script1Param1Spin.setMaximum(2147483647)

        self.horizontalLayout_script1Params.addWidget(self.script1Param1Spin)

        self.script1Param2Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script1Param2Spin.setObjectName("script1Param2Spin")
        sizePolicy1.setHeightForWidth(self.script1Param2Spin.sizePolicy().hasHeightForWidth())
        self.script1Param2Spin.setSizePolicy(sizePolicy1)
        self.script1Param2Spin.setMinimumSize(QSize(30, 0))
        self.script1Param2Spin.setMinimum(-2147483648)
        self.script1Param2Spin.setMaximum(2147483647)

        self.horizontalLayout_script1Params.addWidget(self.script1Param2Spin)

        self.script1Param3Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script1Param3Spin.setObjectName("script1Param3Spin")
        sizePolicy1.setHeightForWidth(self.script1Param3Spin.sizePolicy().hasHeightForWidth())
        self.script1Param3Spin.setSizePolicy(sizePolicy1)
        self.script1Param3Spin.setMinimumSize(QSize(30, 0))
        self.script1Param3Spin.setMinimum(-2147483648)
        self.script1Param3Spin.setMaximum(2147483647)

        self.horizontalLayout_script1Params.addWidget(self.script1Param3Spin)

        self.script1Param4Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script1Param4Spin.setObjectName("script1Param4Spin")
        sizePolicy1.setHeightForWidth(self.script1Param4Spin.sizePolicy().hasHeightForWidth())
        self.script1Param4Spin.setSizePolicy(sizePolicy1)
        self.script1Param4Spin.setMinimumSize(QSize(30, 0))
        self.script1Param4Spin.setMinimum(-2147483648)
        self.script1Param4Spin.setMaximum(2147483647)

        self.horizontalLayout_script1Params.addWidget(self.script1Param4Spin)

        self.script1Param5Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script1Param5Spin.setObjectName("script1Param5Spin")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.script1Param5Spin.sizePolicy().hasHeightForWidth())
        self.script1Param5Spin.setSizePolicy(sizePolicy2)
        self.script1Param5Spin.setMaximumSize(QSize(85, 16777215))

        self.horizontalLayout_script1Params.addWidget(self.script1Param5Spin)

        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_script1Params.addItem(self.horizontalSpacer_9)

        self.script1Param6Edit = QLineEdit(self.scrollAreaWidgetContents)
        self.script1Param6Edit.setObjectName("script1Param6Edit")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.script1Param6Edit.sizePolicy().hasHeightForWidth())
        self.script1Param6Edit.setSizePolicy(sizePolicy3)
        self.script1Param6Edit.setMinimumSize(QSize(0, 0))

        self.horizontalLayout_script1Params.addWidget(self.script1Param6Edit)


        self.verticalLayout_scripts.addLayout(self.horizontalLayout_script1Params)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.script2Label = QLabel(self.scrollAreaWidgetContents)
        self.script2Label.setObjectName("script2Label")
        sizePolicy.setHeightForWidth(self.script2Label.sizePolicy().hasHeightForWidth())
        self.script2Label.setSizePolicy(sizePolicy)
        self.script2Label.setMinimumSize(QSize(100, 0))
        self.script2Label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_2.addWidget(self.script2Label, 0, Qt.AlignLeft)

        self.script2ResrefEdit = FilterComboBox(self.scrollAreaWidgetContents)
        self.script2ResrefEdit.setObjectName("script2ResrefEdit")
        self.script2ResrefEdit.setMinimumSize(QSize(150, 0))
        self.script2ResrefEdit.setMaximumSize(QSize(16777215, 16777215))

        self.horizontalLayout_2.addWidget(self.script2ResrefEdit)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_5)


        self.verticalLayout_scripts.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_script2Params = QHBoxLayout()
        self.horizontalLayout_script2Params.setSpacing(0)
        self.horizontalLayout_script2Params.setObjectName("horizontalLayout_script2Params")
        self.script2Param1Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script2Param1Spin.setObjectName("script2Param1Spin")
        sizePolicy1.setHeightForWidth(self.script2Param1Spin.sizePolicy().hasHeightForWidth())
        self.script2Param1Spin.setSizePolicy(sizePolicy1)
        self.script2Param1Spin.setMinimumSize(QSize(30, 0))
        self.script2Param1Spin.setMinimum(-2147483648)
        self.script2Param1Spin.setMaximum(2147483647)

        self.horizontalLayout_script2Params.addWidget(self.script2Param1Spin)

        self.script2Param2Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script2Param2Spin.setObjectName("script2Param2Spin")
        sizePolicy1.setHeightForWidth(self.script2Param2Spin.sizePolicy().hasHeightForWidth())
        self.script2Param2Spin.setSizePolicy(sizePolicy1)
        self.script2Param2Spin.setMinimumSize(QSize(30, 0))
        self.script2Param2Spin.setMinimum(-2147483648)
        self.script2Param2Spin.setMaximum(2147483647)

        self.horizontalLayout_script2Params.addWidget(self.script2Param2Spin)

        self.script2Param3Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script2Param3Spin.setObjectName("script2Param3Spin")
        sizePolicy1.setHeightForWidth(self.script2Param3Spin.sizePolicy().hasHeightForWidth())
        self.script2Param3Spin.setSizePolicy(sizePolicy1)
        self.script2Param3Spin.setMinimumSize(QSize(30, 0))
        self.script2Param3Spin.setMinimum(-2147483648)
        self.script2Param3Spin.setMaximum(2147483647)

        self.horizontalLayout_script2Params.addWidget(self.script2Param3Spin)

        self.script2Param4Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script2Param4Spin.setObjectName("script2Param4Spin")
        sizePolicy1.setHeightForWidth(self.script2Param4Spin.sizePolicy().hasHeightForWidth())
        self.script2Param4Spin.setSizePolicy(sizePolicy1)
        self.script2Param4Spin.setMinimumSize(QSize(30, 0))
        self.script2Param4Spin.setMinimum(-2147483648)
        self.script2Param4Spin.setMaximum(2147483647)

        self.horizontalLayout_script2Params.addWidget(self.script2Param4Spin)

        self.script2Param5Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.script2Param5Spin.setObjectName("script2Param5Spin")
        sizePolicy1.setHeightForWidth(self.script2Param5Spin.sizePolicy().hasHeightForWidth())
        self.script2Param5Spin.setSizePolicy(sizePolicy1)
        self.script2Param5Spin.setMinimumSize(QSize(30, 0))
        self.script2Param5Spin.setMinimum(-2147483648)
        self.script2Param5Spin.setMaximum(2147483647)

        self.horizontalLayout_script2Params.addWidget(self.script2Param5Spin)

        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_script2Params.addItem(self.horizontalSpacer_8)

        self.script2Param6Edit = QLineEdit(self.scrollAreaWidgetContents)
        self.script2Param6Edit.setObjectName("script2Param6Edit")
        sizePolicy3.setHeightForWidth(self.script2Param6Edit.sizePolicy().hasHeightForWidth())
        self.script2Param6Edit.setSizePolicy(sizePolicy3)

        self.horizontalLayout_script2Params.addWidget(self.script2Param6Edit)


        self.verticalLayout_scripts.addLayout(self.horizontalLayout_script2Params)


        self.verticalLayout_rightDock.addLayout(self.verticalLayout_scripts)

        self.verticalLayout_conditions = QVBoxLayout()
        self.verticalLayout_conditions.setSpacing(2)
        self.verticalLayout_conditions.setObjectName("verticalLayout_conditions")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(2)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.conditional1Label = QLabel(self.scrollAreaWidgetContents)
        self.conditional1Label.setObjectName("conditional1Label")
        sizePolicy.setHeightForWidth(self.conditional1Label.sizePolicy().hasHeightForWidth())
        self.conditional1Label.setSizePolicy(sizePolicy)
        self.conditional1Label.setMinimumSize(QSize(100, 0))

        self.horizontalLayout_3.addWidget(self.conditional1Label)

        self.condition1ResrefEdit = FilterComboBox(self.scrollAreaWidgetContents)
        self.condition1ResrefEdit.setObjectName("condition1ResrefEdit")
        self.condition1ResrefEdit.setMinimumSize(QSize(150, 0))
        self.condition1ResrefEdit.setMaximumSize(QSize(16777215, 16777215))

        self.horizontalLayout_3.addWidget(self.condition1ResrefEdit)

        self.condition1NotCheckbox = QCheckBox(self.scrollAreaWidgetContents)
        self.condition1NotCheckbox.setObjectName("condition1NotCheckbox")

        self.horizontalLayout_3.addWidget(self.condition1NotCheckbox)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_6)


        self.verticalLayout_conditions.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_condition1Params = QHBoxLayout()
        self.horizontalLayout_condition1Params.setSpacing(0)
        self.horizontalLayout_condition1Params.setObjectName("horizontalLayout_condition1Params")
        self.condition1Param1Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition1Param1Spin.setObjectName("condition1Param1Spin")
        sizePolicy1.setHeightForWidth(self.condition1Param1Spin.sizePolicy().hasHeightForWidth())
        self.condition1Param1Spin.setSizePolicy(sizePolicy1)
        self.condition1Param1Spin.setMinimumSize(QSize(30, 0))
        self.condition1Param1Spin.setMinimum(-2147483648)
        self.condition1Param1Spin.setMaximum(2147483647)

        self.horizontalLayout_condition1Params.addWidget(self.condition1Param1Spin)

        self.condition1Param2Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition1Param2Spin.setObjectName("condition1Param2Spin")
        sizePolicy1.setHeightForWidth(self.condition1Param2Spin.sizePolicy().hasHeightForWidth())
        self.condition1Param2Spin.setSizePolicy(sizePolicy1)
        self.condition1Param2Spin.setMinimumSize(QSize(30, 0))
        self.condition1Param2Spin.setMinimum(-2147483648)
        self.condition1Param2Spin.setMaximum(2147483647)

        self.horizontalLayout_condition1Params.addWidget(self.condition1Param2Spin)

        self.condition1Param3Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition1Param3Spin.setObjectName("condition1Param3Spin")
        sizePolicy1.setHeightForWidth(self.condition1Param3Spin.sizePolicy().hasHeightForWidth())
        self.condition1Param3Spin.setSizePolicy(sizePolicy1)
        self.condition1Param3Spin.setMinimumSize(QSize(30, 0))
        self.condition1Param3Spin.setMinimum(-2147483648)
        self.condition1Param3Spin.setMaximum(2147483647)

        self.horizontalLayout_condition1Params.addWidget(self.condition1Param3Spin)

        self.condition1Param4Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition1Param4Spin.setObjectName("condition1Param4Spin")
        sizePolicy1.setHeightForWidth(self.condition1Param4Spin.sizePolicy().hasHeightForWidth())
        self.condition1Param4Spin.setSizePolicy(sizePolicy1)
        self.condition1Param4Spin.setMinimumSize(QSize(30, 0))
        self.condition1Param4Spin.setMinimum(-2147483648)
        self.condition1Param4Spin.setMaximum(2147483647)

        self.horizontalLayout_condition1Params.addWidget(self.condition1Param4Spin)

        self.condition1Param5Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition1Param5Spin.setObjectName("condition1Param5Spin")
        sizePolicy1.setHeightForWidth(self.condition1Param5Spin.sizePolicy().hasHeightForWidth())
        self.condition1Param5Spin.setSizePolicy(sizePolicy1)
        self.condition1Param5Spin.setMinimumSize(QSize(30, 0))
        self.condition1Param5Spin.setMinimum(-2147483648)
        self.condition1Param5Spin.setMaximum(2147483647)

        self.horizontalLayout_condition1Params.addWidget(self.condition1Param5Spin)

        self.condition1Param6Edit = QLineEdit(self.scrollAreaWidgetContents)
        self.condition1Param6Edit.setObjectName("condition1Param6Edit")
        sizePolicy3.setHeightForWidth(self.condition1Param6Edit.sizePolicy().hasHeightForWidth())
        self.condition1Param6Edit.setSizePolicy(sizePolicy3)

        self.horizontalLayout_condition1Params.addWidget(self.condition1Param6Edit)


        self.verticalLayout_conditions.addLayout(self.horizontalLayout_condition1Params)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(2)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.conditional2Label = QLabel(self.scrollAreaWidgetContents)
        self.conditional2Label.setObjectName("conditional2Label")
        sizePolicy.setHeightForWidth(self.conditional2Label.sizePolicy().hasHeightForWidth())
        self.conditional2Label.setSizePolicy(sizePolicy)
        self.conditional2Label.setMinimumSize(QSize(100, 0))

        self.horizontalLayout_4.addWidget(self.conditional2Label)

        self.condition2ResrefEdit = FilterComboBox(self.scrollAreaWidgetContents)
        self.condition2ResrefEdit.setObjectName("condition2ResrefEdit")
        self.condition2ResrefEdit.setMinimumSize(QSize(150, 0))
        self.condition2ResrefEdit.setMaximumSize(QSize(16777215, 16777215))

        self.horizontalLayout_4.addWidget(self.condition2ResrefEdit)

        self.condition2NotCheckbox = QCheckBox(self.scrollAreaWidgetContents)
        self.condition2NotCheckbox.setObjectName("condition2NotCheckbox")

        self.horizontalLayout_4.addWidget(self.condition2NotCheckbox)

        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_7)


        self.verticalLayout_conditions.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(-1, -1, -1, 0)

        self.verticalLayout_conditions.addLayout(self.horizontalLayout_9)

        self.horizontalLayout_condition2Params = QHBoxLayout()
        self.horizontalLayout_condition2Params.setSpacing(0)
        self.horizontalLayout_condition2Params.setObjectName("horizontalLayout_condition2Params")
        self.condition2Param1Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition2Param1Spin.setObjectName("condition2Param1Spin")
        sizePolicy1.setHeightForWidth(self.condition2Param1Spin.sizePolicy().hasHeightForWidth())
        self.condition2Param1Spin.setSizePolicy(sizePolicy1)
        self.condition2Param1Spin.setMinimumSize(QSize(30, 0))
        self.condition2Param1Spin.setMinimum(-2147483648)
        self.condition2Param1Spin.setMaximum(2147483647)

        self.horizontalLayout_condition2Params.addWidget(self.condition2Param1Spin)

        self.condition2Param2Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition2Param2Spin.setObjectName("condition2Param2Spin")
        sizePolicy1.setHeightForWidth(self.condition2Param2Spin.sizePolicy().hasHeightForWidth())
        self.condition2Param2Spin.setSizePolicy(sizePolicy1)
        self.condition2Param2Spin.setMinimumSize(QSize(30, 0))
        self.condition2Param2Spin.setMinimum(-2147483648)
        self.condition2Param2Spin.setMaximum(2147483647)

        self.horizontalLayout_condition2Params.addWidget(self.condition2Param2Spin)

        self.condition2Param3Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition2Param3Spin.setObjectName("condition2Param3Spin")
        sizePolicy1.setHeightForWidth(self.condition2Param3Spin.sizePolicy().hasHeightForWidth())
        self.condition2Param3Spin.setSizePolicy(sizePolicy1)
        self.condition2Param3Spin.setMinimumSize(QSize(30, 0))
        self.condition2Param3Spin.setMinimum(-2147483648)
        self.condition2Param3Spin.setMaximum(2147483647)

        self.horizontalLayout_condition2Params.addWidget(self.condition2Param3Spin)

        self.condition2Param4Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition2Param4Spin.setObjectName("condition2Param4Spin")
        sizePolicy1.setHeightForWidth(self.condition2Param4Spin.sizePolicy().hasHeightForWidth())
        self.condition2Param4Spin.setSizePolicy(sizePolicy1)
        self.condition2Param4Spin.setMinimumSize(QSize(30, 0))
        self.condition2Param4Spin.setMinimum(-2147483648)
        self.condition2Param4Spin.setMaximum(2147483647)

        self.horizontalLayout_condition2Params.addWidget(self.condition2Param4Spin)

        self.condition2Param5Spin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.condition2Param5Spin.setObjectName("condition2Param5Spin")
        sizePolicy1.setHeightForWidth(self.condition2Param5Spin.sizePolicy().hasHeightForWidth())
        self.condition2Param5Spin.setSizePolicy(sizePolicy1)
        self.condition2Param5Spin.setMinimumSize(QSize(30, 0))
        self.condition2Param5Spin.setMinimum(-2147483648)
        self.condition2Param5Spin.setMaximum(2147483647)

        self.horizontalLayout_condition2Params.addWidget(self.condition2Param5Spin)

        self.condition2Param6Edit = QLineEdit(self.scrollAreaWidgetContents)
        self.condition2Param6Edit.setObjectName("condition2Param6Edit")
        sizePolicy3.setHeightForWidth(self.condition2Param6Edit.sizePolicy().hasHeightForWidth())
        self.condition2Param6Edit.setSizePolicy(sizePolicy3)

        self.horizontalLayout_condition2Params.addWidget(self.condition2Param6Edit)


        self.verticalLayout_conditions.addLayout(self.horizontalLayout_condition2Params)


        self.verticalLayout_rightDock.addLayout(self.verticalLayout_conditions)

        self.verticalLayout_anims = QVBoxLayout()
        self.verticalLayout_anims.setSpacing(2)
        self.verticalLayout_anims.setObjectName("verticalLayout_anims")
        self.curAnimsLabel = QLabel(self.scrollAreaWidgetContents)
        self.curAnimsLabel.setObjectName("curAnimsLabel")
        self.curAnimsLabel.setLayoutDirection(Qt.LeftToRight)
        self.curAnimsLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout_anims.addWidget(self.curAnimsLabel, 0, Qt.AlignVCenter)

        self.animsList = QListWidget(self.scrollAreaWidgetContents)
        self.animsList.setObjectName("animsList")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.animsList.sizePolicy().hasHeightForWidth())
        self.animsList.setSizePolicy(sizePolicy4)

        self.verticalLayout_anims.addWidget(self.animsList)

        self.horizontalLayout_animsButtons = QHBoxLayout()
        self.horizontalLayout_animsButtons.setObjectName("horizontalLayout_animsButtons")
        self.addAnimButton = QPushButton(self.scrollAreaWidgetContents)
        self.addAnimButton.setObjectName("addAnimButton")

        self.horizontalLayout_animsButtons.addWidget(self.addAnimButton)

        self.removeAnimButton = QPushButton(self.scrollAreaWidgetContents)
        self.removeAnimButton.setObjectName("removeAnimButton")

        self.horizontalLayout_animsButtons.addWidget(self.removeAnimButton)

        self.editAnimButton = QPushButton(self.scrollAreaWidgetContents)
        self.editAnimButton.setObjectName("editAnimButton")

        self.horizontalLayout_animsButtons.addWidget(self.editAnimButton)


        self.verticalLayout_anims.addLayout(self.horizontalLayout_animsButtons)

        self.formLayout_anims = QFormLayout()
        self.formLayout_anims.setObjectName("formLayout_anims")
        self.emotionSelect = ComboBox2DA(self.scrollAreaWidgetContents)
        self.emotionSelect.setObjectName("emotionSelect")

        self.formLayout_anims.setWidget(0, QFormLayout.FieldRole, self.emotionSelect)

        self.expressionLabel = QLabel(self.scrollAreaWidgetContents)
        self.expressionLabel.setObjectName("expressionLabel")

        self.formLayout_anims.setWidget(1, QFormLayout.LabelRole, self.expressionLabel)

        self.expressionSelect = ComboBox2DA(self.scrollAreaWidgetContents)
        self.expressionSelect.setObjectName("expressionSelect")

        self.formLayout_anims.setWidget(1, QFormLayout.FieldRole, self.expressionSelect)

        self.emotionLabel = QLabel(self.scrollAreaWidgetContents)
        self.emotionLabel.setObjectName("emotionLabel")
        self.emotionLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.formLayout_anims.setWidget(0, QFormLayout.LabelRole, self.emotionLabel)


        self.verticalLayout_anims.addLayout(self.formLayout_anims)

        self.formLayout_sound = QFormLayout()
        self.formLayout_sound.setObjectName("formLayout_sound")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, -1, -1)
        self.soundLabel = QLabel(self.scrollAreaWidgetContents)
        self.soundLabel.setObjectName("soundLabel")
        sizePolicy1.setHeightForWidth(self.soundLabel.sizePolicy().hasHeightForWidth())
        self.soundLabel.setSizePolicy(sizePolicy1)

        self.verticalLayout_2.addWidget(self.soundLabel, 0, Qt.AlignHCenter)

        self.soundCheckbox = QCheckBox(self.scrollAreaWidgetContents)
        self.soundCheckbox.setObjectName("soundCheckbox")
        self.soundCheckbox.setMaximumSize(QSize(250, 16777215))

        self.verticalLayout_2.addWidget(self.soundCheckbox, 0, Qt.AlignHCenter|Qt.AlignTop)


        self.formLayout_sound.setLayout(0, QFormLayout.LabelRole, self.verticalLayout_2)

        self.verticalLayout_sound = QVBoxLayout()
        self.verticalLayout_sound.setSpacing(4)
        self.verticalLayout_sound.setObjectName("verticalLayout_sound")
        self.soundComboBox = FilterComboBox(self.scrollAreaWidgetContents)
        self.soundComboBox.setObjectName("soundComboBox")

        self.verticalLayout_sound.addWidget(self.soundComboBox)

        self.soundButton = QPushButton(self.scrollAreaWidgetContents)
        self.soundButton.setObjectName("soundButton")

        self.verticalLayout_sound.addWidget(self.soundButton)


        self.formLayout_sound.setLayout(0, QFormLayout.FieldRole, self.verticalLayout_sound)

        self.verticalLayout_voice = QVBoxLayout()
        self.verticalLayout_voice.setObjectName("verticalLayout_voice")
        self.voiceComboBox = FilterComboBox(self.scrollAreaWidgetContents)
        self.voiceComboBox.setObjectName("voiceComboBox")

        self.verticalLayout_voice.addWidget(self.voiceComboBox)

        self.voiceButton = QPushButton(self.scrollAreaWidgetContents)
        self.voiceButton.setObjectName("voiceButton")

        self.verticalLayout_voice.addWidget(self.voiceButton)


        self.formLayout_sound.setLayout(2, QFormLayout.FieldRole, self.verticalLayout_voice)

        self.voiceLabel = QLabel(self.scrollAreaWidgetContents)
        self.voiceLabel.setObjectName("voiceLabel")

        self.formLayout_sound.setWidget(2, QFormLayout.LabelRole, self.voiceLabel)


        self.verticalLayout_anims.addLayout(self.formLayout_sound)


        self.verticalLayout_rightDock.addLayout(self.verticalLayout_anims)

        self.verticalLayout_journal = QVBoxLayout()
        self.verticalLayout_journal.setObjectName("verticalLayout_journal")

        self.verticalLayout_rightDock.addLayout(self.verticalLayout_journal)

        self.verticalLayout_camera = QVBoxLayout()
        self.verticalLayout_camera.setObjectName("verticalLayout_camera")
        self.cameraIdLabel = QLabel(self.scrollAreaWidgetContents)
        self.cameraIdLabel.setObjectName("cameraIdLabel")

        self.verticalLayout_camera.addWidget(self.cameraIdLabel)

        self.cameraIdSpin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.cameraIdSpin.setObjectName("cameraIdSpin")
        self.cameraIdSpin.setMinimum(-2147483648)
        self.cameraIdSpin.setMaximum(2147483647)

        self.verticalLayout_camera.addWidget(self.cameraIdSpin)

        self.cameraAnimLabel = QLabel(self.scrollAreaWidgetContents)
        self.cameraAnimLabel.setObjectName("cameraAnimLabel")

        self.verticalLayout_camera.addWidget(self.cameraAnimLabel)

        self.cameraAnimSpin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.cameraAnimSpin.setObjectName("cameraAnimSpin")

        self.verticalLayout_camera.addWidget(self.cameraAnimSpin)

        self.cameraAngleLabel = QLabel(self.scrollAreaWidgetContents)
        self.cameraAngleLabel.setObjectName("cameraAngleLabel")

        self.verticalLayout_camera.addWidget(self.cameraAngleLabel)

        self.cameraAngleSelect = QComboBox(self.scrollAreaWidgetContents)
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.addItem("")
        self.cameraAngleSelect.setObjectName("cameraAngleSelect")

        self.verticalLayout_camera.addWidget(self.cameraAngleSelect)

        self.cameraVidEffectLabel = QLabel(self.scrollAreaWidgetContents)
        self.cameraVidEffectLabel.setObjectName("cameraVidEffectLabel")

        self.verticalLayout_camera.addWidget(self.cameraVidEffectLabel)

        self.cameraEffectSelect = ComboBox2DA(self.scrollAreaWidgetContents)
        self.cameraEffectSelect.setObjectName("cameraEffectSelect")

        self.verticalLayout_camera.addWidget(self.cameraEffectSelect)


        self.verticalLayout_rightDock.addLayout(self.verticalLayout_camera)

        self.verticalLayout_other = QVBoxLayout()
        self.verticalLayout_other.setObjectName("verticalLayout_other")
        self.nodeUnskippableCheckbox = QCheckBox(self.scrollAreaWidgetContents)
        self.nodeUnskippableCheckbox.setObjectName("nodeUnskippableCheckbox")

        self.verticalLayout_other.addWidget(self.nodeUnskippableCheckbox, 0, Qt.AlignHCenter)

        self.formLayout_other = QFormLayout()
        self.formLayout_other.setObjectName("formLayout_other")
        self.formLayout_other.setHorizontalSpacing(2)
        self.formLayout_other.setVerticalSpacing(2)
        self.nodeIdLabel = QLabel(self.scrollAreaWidgetContents)
        self.nodeIdLabel.setObjectName("nodeIdLabel")

        self.formLayout_other.setWidget(0, QFormLayout.LabelRole, self.nodeIdLabel)

        self.nodeIdSpin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.nodeIdSpin.setObjectName("nodeIdSpin")

        self.formLayout_other.setWidget(0, QFormLayout.FieldRole, self.nodeIdSpin)

        self.alienRaceNodeLabel = QLabel(self.scrollAreaWidgetContents)
        self.alienRaceNodeLabel.setObjectName("alienRaceNodeLabel")

        self.formLayout_other.setWidget(1, QFormLayout.LabelRole, self.alienRaceNodeLabel)

        self.alienRaceNodeSpin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.alienRaceNodeSpin.setObjectName("alienRaceNodeSpin")

        self.formLayout_other.setWidget(1, QFormLayout.FieldRole, self.alienRaceNodeSpin)

        self.postProcNodeLabel = QLabel(self.scrollAreaWidgetContents)
        self.postProcNodeLabel.setObjectName("postProcNodeLabel")

        self.formLayout_other.setWidget(2, QFormLayout.LabelRole, self.postProcNodeLabel)

        self.postProcSpin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.postProcSpin.setObjectName("postProcSpin")

        self.formLayout_other.setWidget(2, QFormLayout.FieldRole, self.postProcSpin)

        self.delayNodeLabel = QLabel(self.scrollAreaWidgetContents)
        self.delayNodeLabel.setObjectName("delayNodeLabel")

        self.formLayout_other.setWidget(3, QFormLayout.LabelRole, self.delayNodeLabel)

        self.delaySpin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.delaySpin.setObjectName("delaySpin")

        self.formLayout_other.setWidget(3, QFormLayout.FieldRole, self.delaySpin)

        self.logicLabel = QLabel(self.scrollAreaWidgetContents)
        self.logicLabel.setObjectName("logicLabel")

        self.formLayout_other.setWidget(4, QFormLayout.LabelRole, self.logicLabel)

        self.logicSpin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.logicSpin.setObjectName("logicSpin")

        self.formLayout_other.setWidget(4, QFormLayout.FieldRole, self.logicSpin)

        self.waitFlagsLabel = QLabel(self.scrollAreaWidgetContents)
        self.waitFlagsLabel.setObjectName("waitFlagsLabel")

        self.formLayout_other.setWidget(5, QFormLayout.LabelRole, self.waitFlagsLabel)

        self.waitFlagSpin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.waitFlagSpin.setObjectName("waitFlagSpin")

        self.formLayout_other.setWidget(5, QFormLayout.FieldRole, self.waitFlagSpin)

        self.fadeTypeLabel = QLabel(self.scrollAreaWidgetContents)
        self.fadeTypeLabel.setObjectName("fadeTypeLabel")

        self.formLayout_other.setWidget(6, QFormLayout.LabelRole, self.fadeTypeLabel)

        self.fadeTypeSpin = GFFFieldSpinBox(self.scrollAreaWidgetContents)
        self.fadeTypeSpin.setObjectName("fadeTypeSpin")

        self.formLayout_other.setWidget(6, QFormLayout.FieldRole, self.fadeTypeSpin)


        self.verticalLayout_other.addLayout(self.formLayout_other)


        self.verticalLayout_rightDock.addLayout(self.verticalLayout_other)

        self.verticalLayout_stunts = QVBoxLayout()
        self.verticalLayout_stunts.setObjectName("verticalLayout_stunts")

        self.verticalLayout_rightDock.addLayout(self.verticalLayout_stunts)

        self.scrollArea_rightDock.setWidget(self.scrollAreaWidgetContents)
        self.rightDockWidget.setWidget(self.scrollArea_rightDock)
        MainWindow.addDockWidget(Qt.RightDockWidgetArea, self.rightDockWidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 944, 21))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuTools = QMenu(self.menubar)
        self.menuTools.setObjectName("menuTools")
        MainWindow.setMenuBar(self.menubar)
        self.topDockWidget = QDockWidget(MainWindow)
        self.topDockWidget.setObjectName("topDockWidget")
        self.topDockWidget.setBaseSize(QSize(845, 151))
        self.topDockWidget.setFocusPolicy(Qt.StrongFocus)
        self.topDockWidget.setAllowedAreas(Qt.BottomDockWidgetArea|Qt.TopDockWidgetArea)
        self.topDockWidgetContents = QWidget()
        self.topDockWidgetContents.setObjectName("topDockWidgetContents")
        self.gridLayout_5 = QGridLayout(self.topDockWidgetContents)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SetMinimumSize)
        self.verticalLayout.setContentsMargins(2, -1, 2, -1)
        self.cutsceneModelLabel = QLabel(self.topDockWidgetContents)
        self.cutsceneModelLabel.setObjectName("cutsceneModelLabel")

        self.verticalLayout.addWidget(self.cutsceneModelLabel, 0, Qt.AlignHCenter)

        self.stuntList = QListWidget(self.topDockWidgetContents)
        self.stuntList.setObjectName("stuntList")

        self.verticalLayout.addWidget(self.stuntList)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setSpacing(0)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.horizontalSpacer_10 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_10)

        self.addStuntButton = QPushButton(self.topDockWidgetContents)
        self.addStuntButton.setObjectName("addStuntButton")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.addStuntButton.sizePolicy().hasHeightForWidth())
        self.addStuntButton.setSizePolicy(sizePolicy5)
        self.addStuntButton.setBaseSize(QSize(20, 0))

        self.horizontalLayout_5.addWidget(self.addStuntButton)

        self.editStuntButton = QPushButton(self.topDockWidgetContents)
        self.editStuntButton.setObjectName("editStuntButton")
        sizePolicy5.setHeightForWidth(self.editStuntButton.sizePolicy().hasHeightForWidth())
        self.editStuntButton.setSizePolicy(sizePolicy5)

        self.horizontalLayout_5.addWidget(self.editStuntButton)

        self.removeStuntButton = QPushButton(self.topDockWidgetContents)
        self.removeStuntButton.setObjectName("removeStuntButton")
        sizePolicy5.setHeightForWidth(self.removeStuntButton.sizePolicy().hasHeightForWidth())
        self.removeStuntButton.setSizePolicy(sizePolicy5)

        self.horizontalLayout_5.addWidget(self.removeStuntButton)

        self.horizontalSpacer_11 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_11)


        self.verticalLayout.addLayout(self.horizontalLayout_5)


        self.gridLayout_5.addLayout(self.verticalLayout, 0, 3, 1, 1)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.gridLayout_3.setHorizontalSpacing(5)
        self.gridLayout_3.setVerticalSpacing(3)
        self.gridLayout_3.setContentsMargins(2, -1, 2, -1)
        self.convoTypeLabel = QLabel(self.topDockWidgetContents)
        self.convoTypeLabel.setObjectName("convoTypeLabel")

        self.gridLayout_3.addWidget(self.convoTypeLabel, 0, 0, 1, 1, Qt.AlignRight)

        self.conversationSelect = QComboBox(self.topDockWidgetContents)
        self.conversationSelect.addItem("")
        self.conversationSelect.addItem("")
        self.conversationSelect.addItem("")
        self.conversationSelect.addItem("")
        self.conversationSelect.addItem("")
        self.conversationSelect.setObjectName("conversationSelect")
        sizePolicy6 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.conversationSelect.sizePolicy().hasHeightForWidth())
        self.conversationSelect.setSizePolicy(sizePolicy6)

        self.gridLayout_3.addWidget(self.conversationSelect, 0, 1, 1, 1)

        self.computerTypeLabel = QLabel(self.topDockWidgetContents)
        self.computerTypeLabel.setObjectName("computerTypeLabel")

        self.gridLayout_3.addWidget(self.computerTypeLabel, 1, 0, 1, 1, Qt.AlignRight)

        self.computerSelect = QComboBox(self.topDockWidgetContents)
        self.computerSelect.addItem("")
        self.computerSelect.addItem("")
        self.computerSelect.setObjectName("computerSelect")
        sizePolicy6.setHeightForWidth(self.computerSelect.sizePolicy().hasHeightForWidth())
        self.computerSelect.setSizePolicy(sizePolicy6)

        self.gridLayout_3.addWidget(self.computerSelect, 1, 1, 1, 1)

        self.delayReplyLabel = QLabel(self.topDockWidgetContents)
        self.delayReplyLabel.setObjectName("delayReplyLabel")

        self.gridLayout_3.addWidget(self.delayReplyLabel, 2, 0, 1, 1, Qt.AlignRight)

        self.replyDelaySpin = GFFFieldSpinBox(self.topDockWidgetContents)
        self.replyDelaySpin.setObjectName("replyDelaySpin")
        sizePolicy6.setHeightForWidth(self.replyDelaySpin.sizePolicy().hasHeightForWidth())
        self.replyDelaySpin.setSizePolicy(sizePolicy6)
        self.replyDelaySpin.setMinimum(-2147483648)
        self.replyDelaySpin.setMaximum(2147483647)

        self.gridLayout_3.addWidget(self.replyDelaySpin, 2, 1, 1, 1)

        self.delayEntryLabel = QLabel(self.topDockWidgetContents)
        self.delayEntryLabel.setObjectName("delayEntryLabel")

        self.gridLayout_3.addWidget(self.delayEntryLabel, 3, 0, 1, 1, Qt.AlignRight)

        self.entryDelaySpin = GFFFieldSpinBox(self.topDockWidgetContents)
        self.entryDelaySpin.setObjectName("entryDelaySpin")
        sizePolicy6.setHeightForWidth(self.entryDelaySpin.sizePolicy().hasHeightForWidth())
        self.entryDelaySpin.setSizePolicy(sizePolicy6)
        self.entryDelaySpin.setMinimum(-2147483648)
        self.entryDelaySpin.setMaximum(2147483647)

        self.gridLayout_3.addWidget(self.entryDelaySpin, 3, 1, 1, 1)

        self.voiceOverIDLabel = QLabel(self.topDockWidgetContents)
        self.voiceOverIDLabel.setObjectName("voiceOverIDLabel")

        self.gridLayout_3.addWidget(self.voiceOverIDLabel, 4, 0, 1, 1, Qt.AlignRight)

        self.voIdEdit = QLineEdit(self.topDockWidgetContents)
        self.voIdEdit.setObjectName("voIdEdit")
        sizePolicy7 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.voIdEdit.sizePolicy().hasHeightForWidth())
        self.voIdEdit.setSizePolicy(sizePolicy7)

        self.gridLayout_3.addWidget(self.voIdEdit, 4, 1, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_3.addItem(self.verticalSpacer_2, 5, 1, 1, 1)


        self.gridLayout_5.addLayout(self.gridLayout_3, 0, 1, 1, 1)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout_2.setSizeConstraint(QLayout.SetMinimumSize)
        self.gridLayout_2.setHorizontalSpacing(5)
        self.gridLayout_2.setVerticalSpacing(4)
        self.gridLayout_2.setContentsMargins(2, -1, 2, -1)
        self.ambientTrackCombo = FilterComboBox(self.topDockWidgetContents)
        self.ambientTrackCombo.setObjectName("ambientTrackCombo")

        self.gridLayout_2.addWidget(self.ambientTrackCombo, 4, 1, 1, 1)

        self.cameraModelSelect = FilterComboBox(self.topDockWidgetContents)
        self.cameraModelSelect.setObjectName("cameraModelSelect")

        self.gridLayout_2.addWidget(self.cameraModelSelect, 2, 1, 1, 1)

        self.onAbortCombo = FilterComboBox(self.topDockWidgetContents)
        self.onAbortCombo.setObjectName("onAbortCombo")
        self.onAbortCombo.setMinimumSize(QSize(160, 0))

        self.gridLayout_2.addWidget(self.onAbortCombo, 0, 1, 1, 1)

        self.onEndEdit = FilterComboBox(self.topDockWidgetContents)
        self.onEndEdit.setObjectName("onEndEdit")
        self.onEndEdit.setMinimumSize(QSize(160, 0))

        self.gridLayout_2.addWidget(self.onEndEdit, 1, 1, 1, 1)

        self.cameraModelLabel = QLabel(self.topDockWidgetContents)
        self.cameraModelLabel.setObjectName("cameraModelLabel")
        sizePolicy8 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy8.setHorizontalStretch(0)
        sizePolicy8.setVerticalStretch(0)
        sizePolicy8.setHeightForWidth(self.cameraModelLabel.sizePolicy().hasHeightForWidth())
        self.cameraModelLabel.setSizePolicy(sizePolicy8)

        self.gridLayout_2.addWidget(self.cameraModelLabel, 2, 0, 1, 1, Qt.AlignRight)

        self.convoEndsScriptLabel = QLabel(self.topDockWidgetContents)
        self.convoEndsScriptLabel.setObjectName("convoEndsScriptLabel")
        sizePolicy8.setHeightForWidth(self.convoEndsScriptLabel.sizePolicy().hasHeightForWidth())
        self.convoEndsScriptLabel.setSizePolicy(sizePolicy8)

        self.gridLayout_2.addWidget(self.convoEndsScriptLabel, 1, 0, 1, 1, Qt.AlignRight)

        self.convoAbortsScriptLabel = QLabel(self.topDockWidgetContents)
        self.convoAbortsScriptLabel.setObjectName("convoAbortsScriptLabel")
        sizePolicy8.setHeightForWidth(self.convoAbortsScriptLabel.sizePolicy().hasHeightForWidth())
        self.convoAbortsScriptLabel.setSizePolicy(sizePolicy8)

        self.gridLayout_2.addWidget(self.convoAbortsScriptLabel, 0, 0, 1, 1, Qt.AlignRight)

        self.ambientTrackLabel = QLabel(self.topDockWidgetContents)
        self.ambientTrackLabel.setObjectName("ambientTrackLabel")
        sizePolicy8.setHeightForWidth(self.ambientTrackLabel.sizePolicy().hasHeightForWidth())
        self.ambientTrackLabel.setSizePolicy(sizePolicy8)

        self.gridLayout_2.addWidget(self.ambientTrackLabel, 4, 0, 1, 1, Qt.AlignRight)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_2.addItem(self.verticalSpacer, 5, 1, 1, 1)


        self.gridLayout_5.addLayout(self.gridLayout_2, 0, 2, 1, 1)

        self.widget = QWidget(self.topDockWidgetContents)
        self.widget.setObjectName("widget")
        sizePolicy9 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy9.setHorizontalStretch(0)
        sizePolicy9.setVerticalStretch(0)
        sizePolicy9.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy9)
        self.widget.setLayoutDirection(Qt.RightToLeft)
        self.gridLayout_4 = QGridLayout(self.widget)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.gridLayout_4.setSizeConstraint(QLayout.SetMinimumSize)
        self.gridLayout_4.setContentsMargins(0, 10, 10, 0)
        self.animatedCutCheckbox = QCheckBox(self.widget)
        self.animatedCutCheckbox.setObjectName("animatedCutCheckbox")
        sizePolicy9.setHeightForWidth(self.animatedCutCheckbox.sizePolicy().hasHeightForWidth())
        self.animatedCutCheckbox.setSizePolicy(sizePolicy9)

        self.gridLayout_4.addWidget(self.animatedCutCheckbox, 3, 0, 1, 1, Qt.AlignLeft|Qt.AlignVCenter)

        self.unequipHandsCheckbox = QCheckBox(self.widget)
        self.unequipHandsCheckbox.setObjectName("unequipHandsCheckbox")

        self.gridLayout_4.addWidget(self.unequipHandsCheckbox, 0, 0, 1, 1, Qt.AlignRight|Qt.AlignVCenter)

        self.unequipAllCheckbox = QCheckBox(self.widget)
        self.unequipAllCheckbox.setObjectName("unequipAllCheckbox")
        sizePolicy9.setHeightForWidth(self.unequipAllCheckbox.sizePolicy().hasHeightForWidth())
        self.unequipAllCheckbox.setSizePolicy(sizePolicy9)

        self.gridLayout_4.addWidget(self.unequipAllCheckbox, 1, 0, 1, 1, Qt.AlignLeft|Qt.AlignVCenter)

        self.oldHitCheckbox = QCheckBox(self.widget)
        self.oldHitCheckbox.setObjectName("oldHitCheckbox")
        sizePolicy9.setHeightForWidth(self.oldHitCheckbox.sizePolicy().hasHeightForWidth())
        self.oldHitCheckbox.setSizePolicy(sizePolicy9)

        self.gridLayout_4.addWidget(self.oldHitCheckbox, 4, 0, 1, 1, Qt.AlignLeft|Qt.AlignVCenter)

        self.skippableCheckbox = QCheckBox(self.widget)
        self.skippableCheckbox.setObjectName("skippableCheckbox")
        sizePolicy9.setHeightForWidth(self.skippableCheckbox.sizePolicy().hasHeightForWidth())
        self.skippableCheckbox.setSizePolicy(sizePolicy9)

        self.gridLayout_4.addWidget(self.skippableCheckbox, 2, 0, 1, 1, Qt.AlignLeft|Qt.AlignVCenter)

        self.verticalSpacer_5 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_4.addItem(self.verticalSpacer_5, 5, 0, 1, 1)


        self.gridLayout_5.addWidget(self.widget, 0, 0, 1, 1)

        self.horizontalSpacer_12 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_5.addItem(self.horizontalSpacer_12, 0, 4, 1, 1)

        self.topDockWidget.setWidget(self.topDockWidgetContents)
        MainWindow.addDockWidget(Qt.TopDockWidgetArea, self.topDockWidget)
        self.dockWidget = QDockWidget(MainWindow)
        self.dockWidget.setObjectName("dockWidget")
        self.dockWidget.setAllowedAreas(Qt.BottomDockWidgetArea|Qt.TopDockWidgetArea)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.gridLayout = QGridLayout(self.dockWidgetContents)
        self.gridLayout.setObjectName("gridLayout")
        self.plotIndexLabel = QLabel(self.dockWidgetContents)
        self.plotIndexLabel.setObjectName("plotIndexLabel")

        self.gridLayout.addWidget(self.plotIndexLabel, 3, 2, 1, 1, Qt.AlignRight)

        self.horizontalSpacer_3 = QSpacerItem(788, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_3, 3, 4, 1, 1)

        self.horizontalSpacer = QSpacerItem(788, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 2, 4, 1, 1)

        self.speakerEditLabel = QLabel(self.dockWidgetContents)
        self.speakerEditLabel.setObjectName("speakerEditLabel")

        self.gridLayout.addWidget(self.speakerEditLabel, 2, 0, 1, 1, Qt.AlignRight)

        self.plotIndexCombo = ComboBox2DA(self.dockWidgetContents)
        self.plotIndexCombo.setObjectName("plotIndexCombo")

        self.gridLayout.addWidget(self.plotIndexCombo, 3, 3, 1, 1)

        self.listenerTagLabel = QLabel(self.dockWidgetContents)
        self.listenerTagLabel.setObjectName("listenerTagLabel")
        sizePolicy10 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy10.setHorizontalStretch(0)
        sizePolicy10.setVerticalStretch(0)
        sizePolicy10.setHeightForWidth(self.listenerTagLabel.sizePolicy().hasHeightForWidth())
        self.listenerTagLabel.setSizePolicy(sizePolicy10)

        self.gridLayout.addWidget(self.listenerTagLabel, 1, 0, 1, 1, Qt.AlignRight)

        self.questLabel = QLabel(self.dockWidgetContents)
        self.questLabel.setObjectName("questLabel")

        self.gridLayout.addWidget(self.questLabel, 1, 2, 1, 1, Qt.AlignRight)

        self.questEntryLabel = QLabel(self.dockWidgetContents)
        self.questEntryLabel.setObjectName("questEntryLabel")

        self.gridLayout.addWidget(self.questEntryLabel, 2, 2, 1, 1, Qt.AlignRight)

        self.horizontalSpacer_2 = QSpacerItem(788, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_2, 1, 4, 1, 1)

        self.plotXpPercentLabel = QLabel(self.dockWidgetContents)
        self.plotXpPercentLabel.setObjectName("plotXpPercentLabel")

        self.gridLayout.addWidget(self.plotXpPercentLabel, 3, 0, 1, 1)

        self.listenerEdit = QLineEdit(self.dockWidgetContents)
        self.listenerEdit.setObjectName("listenerEdit")
        sizePolicy11 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy11.setHorizontalStretch(0)
        sizePolicy11.setVerticalStretch(0)
        sizePolicy11.setHeightForWidth(self.listenerEdit.sizePolicy().hasHeightForWidth())
        self.listenerEdit.setSizePolicy(sizePolicy11)
        self.listenerEdit.setMinimumSize(QSize(150, 0))
        self.listenerEdit.setMaximumSize(QSize(250, 16777215))

        self.gridLayout.addWidget(self.listenerEdit, 1, 1, 1, 1)

        self.questEdit = QLineEdit(self.dockWidgetContents)
        self.questEdit.setObjectName("questEdit")
        sizePolicy11.setHeightForWidth(self.questEdit.sizePolicy().hasHeightForWidth())
        self.questEdit.setSizePolicy(sizePolicy11)
        self.questEdit.setMinimumSize(QSize(150, 0))
        self.questEdit.setMaximumSize(QSize(250, 16777215))

        self.gridLayout.addWidget(self.questEdit, 1, 3, 1, 1)

        self.speakerEdit = QLineEdit(self.dockWidgetContents)
        self.speakerEdit.setObjectName("speakerEdit")
        sizePolicy11.setHeightForWidth(self.speakerEdit.sizePolicy().hasHeightForWidth())
        self.speakerEdit.setSizePolicy(sizePolicy11)
        self.speakerEdit.setMinimumSize(QSize(150, 0))
        self.speakerEdit.setMaximumSize(QSize(250, 16777215))

        self.gridLayout.addWidget(self.speakerEdit, 2, 1, 1, 1)

        self.questEntrySpin = GFFFieldSpinBox(self.dockWidgetContents)
        self.questEntrySpin.setObjectName("questEntrySpin")
        self.questEntrySpin.setMinimumSize(QSize(150, 0))
        self.questEntrySpin.setMaximumSize(QSize(250, 16777215))

        self.gridLayout.addWidget(self.questEntrySpin, 2, 3, 1, 1)

        self.plotXpSpin = QDoubleSpinBox(self.dockWidgetContents)
        self.plotXpSpin.setObjectName("plotXpSpin")
        sizePolicy11.setHeightForWidth(self.plotXpSpin.sizePolicy().hasHeightForWidth())
        self.plotXpSpin.setSizePolicy(sizePolicy11)
        self.plotXpSpin.setMinimumSize(QSize(150, 0))
        self.plotXpSpin.setMaximumSize(QSize(250, 16777215))

        self.gridLayout.addWidget(self.plotXpSpin, 3, 1, 1, 1)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer_3, 4, 3, 1, 1)

        self.dockWidget.setWidget(self.dockWidgetContents)
        self.plotIndexLabel.raise_()
        self.speakerEditLabel.raise_()
        self.plotIndexCombo.raise_()
        self.questLabel.raise_()
        self.questEntryLabel.raise_()
        self.plotXpPercentLabel.raise_()
        self.listenerEdit.raise_()
        self.questEdit.raise_()
        self.speakerEdit.raise_()
        self.questEntrySpin.raise_()
        self.plotXpSpin.raise_()
        self.listenerTagLabel.raise_()
        MainWindow.addDockWidget(Qt.BottomDockWidgetArea, self.dockWidget)

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
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", "DLGEditor", None))
        self.actionNew.setText(QCoreApplication.translate("MainWindow", "New", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", "Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", "Save", None))
        self.actionSaveAs.setText(QCoreApplication.translate("MainWindow", "Save As", None))
        self.actionRevert.setText(QCoreApplication.translate("MainWindow", "Revert", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", "Exit", None))
        self.actionReloadTree.setText(QCoreApplication.translate("MainWindow", "Reload Tree", None))
        self.actionUnfocus.setText(QCoreApplication.translate("MainWindow", "Unfocus Tree", None))
        self.rightDockWidget.setWindowTitle(QCoreApplication.translate("MainWindow", "Node Fields", None))
        self.commentsEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", "Comments", None))
        self.script1Label.setText(QCoreApplication.translate("MainWindow", "Script #1:", None))
        self.script2Label.setText(QCoreApplication.translate("MainWindow", "Script #2:", None))
        self.conditional1Label.setText(QCoreApplication.translate("MainWindow", "Conditional #1:", None))
        self.condition1NotCheckbox.setText(QCoreApplication.translate("MainWindow", "Not", None))
#if QT_CONFIG(tooltip)
        self.condition1Param2Spin.setToolTip(QCoreApplication.translate("MainWindow", "Param2", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.condition1Param3Spin.setToolTip(QCoreApplication.translate("MainWindow", "Param3", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.condition1Param4Spin.setToolTip(QCoreApplication.translate("MainWindow", "Param4", None))
#endif // QT_CONFIG(tooltip)
        self.conditional2Label.setText(QCoreApplication.translate("MainWindow", "Conditional #2:", None))
        self.condition2NotCheckbox.setText(QCoreApplication.translate("MainWindow", "Not", None))
        self.curAnimsLabel.setText(QCoreApplication.translate("MainWindow", "Current Animations", None))
        self.addAnimButton.setText(QCoreApplication.translate("MainWindow", "Add", None))
        self.removeAnimButton.setText(QCoreApplication.translate("MainWindow", "Remove", None))
        self.editAnimButton.setText(QCoreApplication.translate("MainWindow", "Edit", None))
        self.expressionLabel.setText(QCoreApplication.translate("MainWindow", "Expression:", None))
        self.emotionLabel.setText(QCoreApplication.translate("MainWindow", "Emotion:", None))
        self.soundLabel.setText(QCoreApplication.translate("MainWindow", "Sound:", None))
#if QT_CONFIG(tooltip)
        self.soundCheckbox.setToolTip(QCoreApplication.translate("MainWindow", "'SoundExists' field", None))
#endif // QT_CONFIG(tooltip)
        self.soundCheckbox.setText(QCoreApplication.translate("MainWindow", "Exists", None))
        self.soundButton.setText(QCoreApplication.translate("MainWindow", "Play", None))
        self.voiceButton.setText(QCoreApplication.translate("MainWindow", "Play", None))
        self.voiceLabel.setText(QCoreApplication.translate("MainWindow", "Voice:", None))
        self.cameraIdLabel.setText(QCoreApplication.translate("MainWindow", "Camera ID:", None))
        self.cameraAnimLabel.setText(QCoreApplication.translate("MainWindow", "Camera Animation:", None))
        self.cameraAngleLabel.setText(QCoreApplication.translate("MainWindow", "Camera Angle:", None))
        self.cameraAngleSelect.setItemText(0, QCoreApplication.translate("MainWindow", "Auto", None))
        self.cameraAngleSelect.setItemText(1, QCoreApplication.translate("MainWindow", "Face", None))
        self.cameraAngleSelect.setItemText(2, QCoreApplication.translate("MainWindow", "Shoulder", None))
        self.cameraAngleSelect.setItemText(3, QCoreApplication.translate("MainWindow", "Wide Shot", None))
        self.cameraAngleSelect.setItemText(4, QCoreApplication.translate("MainWindow", "Animated Camera", None))
        self.cameraAngleSelect.setItemText(5, QCoreApplication.translate("MainWindow", "(DO NOT USE THIS ENTRY)", None))
        self.cameraAngleSelect.setItemText(6, QCoreApplication.translate("MainWindow", "Static Camera", None))

        self.cameraVidEffectLabel.setText(QCoreApplication.translate("MainWindow", "Camera Video Effect:", None))
        self.nodeUnskippableCheckbox.setText(QCoreApplication.translate("MainWindow", "Node Unskippable", None))
        self.nodeIdLabel.setText(QCoreApplication.translate("MainWindow", "Node ID:", None))
        self.alienRaceNodeLabel.setText(QCoreApplication.translate("MainWindow", "Alien Race Node:", None))
        self.postProcNodeLabel.setText(QCoreApplication.translate("MainWindow", "Post Proc Node:", None))
        self.delayNodeLabel.setText(QCoreApplication.translate("MainWindow", "Delay:", None))
        self.logicLabel.setText(QCoreApplication.translate("MainWindow", "Logic:", None))
        self.waitFlagsLabel.setText(QCoreApplication.translate("MainWindow", "Wait Flags:", None))
        self.fadeTypeLabel.setText(QCoreApplication.translate("MainWindow", "Fade Type:", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", "File", None))
        self.menuTools.setTitle(QCoreApplication.translate("MainWindow", "Tools", None))
        self.topDockWidget.setWindowTitle(QCoreApplication.translate("MainWindow", "File Globals", None))
        self.cutsceneModelLabel.setText(QCoreApplication.translate("MainWindow", "Cutscene Model", None))
#if QT_CONFIG(tooltip)
        self.stuntList.setToolTip(QCoreApplication.translate("MainWindow", "<html><head/><body><p>Dialogue Stunts list</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.addStuntButton.setText(QCoreApplication.translate("MainWindow", "Add", None))
        self.editStuntButton.setText(QCoreApplication.translate("MainWindow", "Edit", None))
        self.removeStuntButton.setText(QCoreApplication.translate("MainWindow", "Remove", None))
        self.convoTypeLabel.setText(QCoreApplication.translate("MainWindow", "Conversation Type:", None))
        self.conversationSelect.setItemText(0, QCoreApplication.translate("MainWindow", "Human", None))
        self.conversationSelect.setItemText(1, QCoreApplication.translate("MainWindow", "Computer", None))
        self.conversationSelect.setItemText(2, QCoreApplication.translate("MainWindow", "Type 3", None))
        self.conversationSelect.setItemText(3, QCoreApplication.translate("MainWindow", "Type 4", None))
        self.conversationSelect.setItemText(4, QCoreApplication.translate("MainWindow", "Type 5", None))

        self.computerTypeLabel.setText(QCoreApplication.translate("MainWindow", "Computer Type:", None))
        self.computerSelect.setItemText(0, QCoreApplication.translate("MainWindow", "Modern", None))
        self.computerSelect.setItemText(1, QCoreApplication.translate("MainWindow", "Ancient", None))

        self.delayReplyLabel.setText(QCoreApplication.translate("MainWindow", "Delay before Reply:", None))
        self.delayEntryLabel.setText(QCoreApplication.translate("MainWindow", "Delay before Entry:", None))
        self.voiceOverIDLabel.setText(QCoreApplication.translate("MainWindow", "Voiceover ID:", None))
        self.cameraModelLabel.setText(QCoreApplication.translate("MainWindow", "Camera Model:", None))
        self.convoEndsScriptLabel.setText(QCoreApplication.translate("MainWindow", "Conversation Ends:", None))
        self.convoAbortsScriptLabel.setText(QCoreApplication.translate("MainWindow", "Conversation Aborts:", None))
        self.ambientTrackLabel.setText(QCoreApplication.translate("MainWindow", "Ambient Track:", None))
        self.animatedCutCheckbox.setText(QCoreApplication.translate("MainWindow", "Animated Cut", None))
        self.unequipHandsCheckbox.setText(QCoreApplication.translate("MainWindow", "Unequip Hands", None))
        self.unequipAllCheckbox.setText(QCoreApplication.translate("MainWindow", "Unequip All", None))
        self.oldHitCheckbox.setText(QCoreApplication.translate("MainWindow", "Old Hit Check", None))
        self.skippableCheckbox.setText(QCoreApplication.translate("MainWindow", "Skippable", None))
#if QT_CONFIG(whatsthis)
        self.plotIndexLabel.setWhatsThis(QCoreApplication.translate("MainWindow", "GFF Field \"PlotIndex\" Int32", None))
#endif // QT_CONFIG(whatsthis)
        self.plotIndexLabel.setText(QCoreApplication.translate("MainWindow", "Plot Index:", None))
        self.speakerEditLabel.setText(QCoreApplication.translate("MainWindow", "Speaker Tag:", None))
        self.listenerTagLabel.setText(QCoreApplication.translate("MainWindow", "Listener Tag:", None))
        self.questLabel.setText(QCoreApplication.translate("MainWindow", "Quest:", None))
        self.questEntryLabel.setText(QCoreApplication.translate("MainWindow", "Quest Entry:", None))
        self.plotXpPercentLabel.setText(QCoreApplication.translate("MainWindow", "Plot XP Percentage", None))
    # retranslateUi

