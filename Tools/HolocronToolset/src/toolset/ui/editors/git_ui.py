
################################################################################
## Form generated from reading UI file 'git.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize, Qt
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMenu,
    QMenuBar,
    QSizePolicy,
    QSpacerItem,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from toolset.gui.widgets.renderer.walkmesh import WalkmeshRenderer


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(838, 648)
        self.actionUndo = QAction(MainWindow)
        self.actionUndo.setObjectName("actionUndo")
        self.actionRedo = QAction(MainWindow)
        self.actionRedo.setObjectName("actionRedo")
        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName("actionNew")
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.actionSave_As = QAction(MainWindow)
        self.actionSave_As.setObjectName("actionSave_As")
        self.actionRevert = QAction(MainWindow)
        self.actionRevert.setObjectName("actionRevert")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionZoomIn = QAction(MainWindow)
        self.actionZoomIn.setObjectName("actionZoomIn")
        self.actionZoomOut = QAction(MainWindow)
        self.actionZoomOut.setObjectName("actionZoomOut")
        self.actionRecentreCamera = QAction(MainWindow)
        self.actionRecentreCamera.setObjectName("actionRecentreCamera")
        self.actionDeleteSelected = QAction(MainWindow)
        self.actionDeleteSelected.setObjectName("actionDeleteSelected")
        self.actionUseWaypointResRef = QAction(MainWindow)
        self.actionUseWaypointResRef.setObjectName("actionUseWaypointResRef")
        self.actionUseWaypointName = QAction(MainWindow)
        self.actionUseWaypointName.setObjectName("actionUseWaypointName")
        self.actionUseWaypointTag = QAction(MainWindow)
        self.actionUseWaypointTag.setObjectName("actionUseWaypointTag")
        self.actionUseTriggerResRef = QAction(MainWindow)
        self.actionUseTriggerResRef.setObjectName("actionUseTriggerResRef")
        self.actionUseTriggerTag = QAction(MainWindow)
        self.actionUseTriggerTag.setObjectName("actionUseTriggerTag")
        self.actionUseDoorResRef = QAction(MainWindow)
        self.actionUseDoorResRef.setObjectName("actionUseDoorResRef")
        self.actionUseDoorTag = QAction(MainWindow)
        self.actionUseDoorTag.setObjectName("actionUseDoorTag")
        self.actionUseCreatureResRef = QAction(MainWindow)
        self.actionUseCreatureResRef.setObjectName("actionUseCreatureResRef")
        self.actionUseCreatureName = QAction(MainWindow)
        self.actionUseCreatureName.setObjectName("actionUseCreatureName")
        self.actionUseCreatureTag = QAction(MainWindow)
        self.actionUseCreatureTag.setObjectName("actionUseCreatureTag")
        self.actionUseDoorName = QAction(MainWindow)
        self.actionUseDoorName.setObjectName("actionUseDoorName")
        self.actionUseDoorResTag = QAction(MainWindow)
        self.actionUseDoorResTag.setObjectName("actionUseDoorResTag")
        self.actionUseWaypointResName = QAction(MainWindow)
        self.actionUseWaypointResName.setObjectName("actionUseWaypointResName")
        self.actionUseWaypointResTag = QAction(MainWindow)
        self.actionUseWaypointResTag.setObjectName("actionUseWaypointResTag")
        self.actionUseTriggerName = QAction(MainWindow)
        self.actionUseTriggerName.setObjectName("actionUseTriggerName")
        self.actionUseTriggerResTag = QAction(MainWindow)
        self.actionUseTriggerResTag.setObjectName("actionUseTriggerResTag")
        self.actionUsePlaceableResRef = QAction(MainWindow)
        self.actionUsePlaceableResRef.setObjectName("actionUsePlaceableResRef")
        self.actionUsePlaceableTag = QAction(MainWindow)
        self.actionUsePlaceableTag.setObjectName("actionUsePlaceableTag")
        self.actionUsePlaceableName = QAction(MainWindow)
        self.actionUsePlaceableName.setObjectName("actionUsePlaceableName")
        self.actionUseMerchantResRef = QAction(MainWindow)
        self.actionUseMerchantResRef.setObjectName("actionUseMerchantResRef")
        self.actionUseMerchantName = QAction(MainWindow)
        self.actionUseMerchantName.setObjectName("actionUseMerchantName")
        self.actionUseMerchantTag = QAction(MainWindow)
        self.actionUseMerchantTag.setObjectName("actionUseMerchantTag")
        self.actionUseSoundResRef = QAction(MainWindow)
        self.actionUseSoundResRef.setObjectName("actionUseSoundResRef")
        self.actionUseSoundName = QAction(MainWindow)
        self.actionUseSoundName.setObjectName("actionUseSoundName")
        self.actionUseSoundTag = QAction(MainWindow)
        self.actionUseSoundTag.setObjectName("actionUseSoundTag")
        self.actionUseEncounterResRef = QAction(MainWindow)
        self.actionUseEncounterResRef.setObjectName("actionUseEncounterResRef")
        self.actionUseEncounterName = QAction(MainWindow)
        self.actionUseEncounterName.setObjectName("actionUseEncounterName")
        self.actionUseEncounterTag = QAction(MainWindow)
        self.actionUseEncounterTag.setObjectName("actionUseEncounterTag")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.splitter = QSplitter(self.centralwidget)
        self.splitter.setObjectName("splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.layoutWidget = QWidget(self.splitter)
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout = QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.filterEdit = QLineEdit(self.layoutWidget)
        self.filterEdit.setObjectName("filterEdit")
        self.filterEdit.setMaxLength(16)

        self.verticalLayout.addWidget(self.filterEdit)

        self.listWidget = QListWidget(self.layoutWidget)
        self.listWidget.setObjectName("listWidget")
        self.listWidget.setMaximumSize(QSize(16777215, 16777215))
        self.listWidget.setContextMenuPolicy(Qt.CustomContextMenu)

        self.verticalLayout.addWidget(self.listWidget)

        self.splitter.addWidget(self.layoutWidget)
        self.layoutWidget1 = QWidget(self.splitter)
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.verticalLayout_2 = QVBoxLayout(self.layoutWidget1)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.lockInstancesCheck = QCheckBox(self.layoutWidget1)
        self.lockInstancesCheck.setObjectName("lockInstancesCheck")
        self.lockInstancesCheck.setMaximumSize(QSize(28, 16777215))
        self.lockInstancesCheck.setStyleSheet("QCheckbox {\n"
"	spacing: 0px;\n"
"}\n"
"\n"
"QCheckBox::indicator {\n"
"    image: url(:/images/icons/lock.png);\n"
"	border: 1px solid rgba(30, 144, 255, 0.0);\n"
"	width: 26px;\n"
"	height: 26px;\n"
"}\n"
"\n"
"QCheckBox::indicator:unchecked:hover {\n"
"	background: rgba(30, 144, 255, 0.2);\n"
"	border: 1px solid rgba(30, 144, 255, 0.4);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked {\n"
"	background: rgba(30, 144, 255, 0.4);\n"
"	border:1px solid rgba(30, 144, 255, 0.6);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked:hover {\n"
"	background: rgba(30, 144, 255, 0.5);\n"
"	border:1px solid rgba(30, 144, 255, 0.7);\n"
"}\n"
"\n"
"")
        self.lockInstancesCheck.setChecked(False)

        self.horizontalLayout_2.addWidget(self.lockInstancesCheck)

        self.label = QLabel(self.layoutWidget1)
        self.label.setObjectName("label")
        self.label.setMaximumSize(QSize(16777215, 28))
        font = QFont()
        font.setPointSize(12)
        self.label.setFont(font)

        self.horizontalLayout_2.addWidget(self.label)

        self.viewCreatureCheck = QCheckBox(self.layoutWidget1)
        self.viewCreatureCheck.setObjectName("viewCreatureCheck")
        self.viewCreatureCheck.setMaximumSize(QSize(28, 16777215))
        self.viewCreatureCheck.setStyleSheet("QCheckbox {\n"
"	spacing: 0px;\n"
"}\n"
"\n"
"QCheckBox::indicator {\n"
"    image: url(:/images/icons/k1/creature.png);\n"
"	border: 1px solid rgba(30, 144, 255, 0.0);\n"
"	width: 26px;\n"
"	height: 26px;\n"
"}\n"
"\n"
"QCheckBox::indicator:unchecked:hover {\n"
"	background: rgba(30, 144, 255, 0.2);\n"
"	border: 1px solid rgba(30, 144, 255, 0.4);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked {\n"
"	background: rgba(30, 144, 255, 0.4);\n"
"	border:1px solid rgba(30, 144, 255, 0.6);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked:hover {\n"
"	background: rgba(30, 144, 255, 0.5);\n"
"	border:1px solid rgba(30, 144, 255, 0.7);\n"
"}\n"
"\n"
"")
        self.viewCreatureCheck.setChecked(True)

        self.horizontalLayout_2.addWidget(self.viewCreatureCheck)

        self.viewDoorCheck = QCheckBox(self.layoutWidget1)
        self.viewDoorCheck.setObjectName("viewDoorCheck")
        self.viewDoorCheck.setMaximumSize(QSize(28, 16777215))
        self.viewDoorCheck.setStyleSheet("QCheckBox::indicator {\n"
"    image: url(:/images/icons/k1/door.png);\n"
"	border: 1px solid rgba(30, 144, 255, 0.0);\n"
"	width: 26px;\n"
"	height: 26px;\n"
"}\n"
"\n"
"QCheckBox::indicator:unchecked:hover {\n"
"	background: rgba(30, 144, 255, 0.2);\n"
"	border: 1px solid rgba(30, 144, 255, 0.4);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked {\n"
"	background: rgba(30, 144, 255, 0.4);\n"
"	border:1px solid rgba(30, 144, 255, 0.6);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked:hover {\n"
"	background: rgba(30, 144, 255, 0.5);\n"
"	border:1px solid rgba(30, 144, 255, 0.7);\n"
"}\n"
"\n"
"")
        self.viewDoorCheck.setChecked(True)

        self.horizontalLayout_2.addWidget(self.viewDoorCheck)

        self.viewPlaceableCheck = QCheckBox(self.layoutWidget1)
        self.viewPlaceableCheck.setObjectName("viewPlaceableCheck")
        self.viewPlaceableCheck.setMaximumSize(QSize(28, 16777215))
        self.viewPlaceableCheck.setStyleSheet("QCheckBox::indicator {\n"
"    image: url(:/images/icons/k1/placeable.png);\n"
"	border: 1px solid rgba(30, 144, 255, 0.0);\n"
"	width: 26px;\n"
"	height: 26px;\n"
"}\n"
"\n"
"QCheckBox::indicator:unchecked:hover {\n"
"	background: rgba(30, 144, 255, 0.2);\n"
"	border: 1px solid rgba(30, 144, 255, 0.4);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked {\n"
"	background: rgba(30, 144, 255, 0.4);\n"
"	border:1px solid rgba(30, 144, 255, 0.6);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked:hover {\n"
"	background: rgba(30, 144, 255, 0.5);\n"
"	border:1px solid rgba(30, 144, 255, 0.7);\n"
"}\n"
"\n"
"")
        self.viewPlaceableCheck.setChecked(True)

        self.horizontalLayout_2.addWidget(self.viewPlaceableCheck)

        self.viewStoreCheck = QCheckBox(self.layoutWidget1)
        self.viewStoreCheck.setObjectName("viewStoreCheck")
        self.viewStoreCheck.setMaximumSize(QSize(28, 16777215))
        self.viewStoreCheck.setStyleSheet("QCheckBox::indicator {\n"
"    image: url(:/images/icons/k1/merchant.png);\n"
"	border: 1px solid rgba(30, 144, 255, 0.0);\n"
"	width: 26px;\n"
"	height: 26px;\n"
"}\n"
"\n"
"QCheckBox::indicator:unchecked:hover {\n"
"	background: rgba(30, 144, 255, 0.2);\n"
"	border: 1px solid rgba(30, 144, 255, 0.4);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked {\n"
"	background: rgba(30, 144, 255, 0.4);\n"
"	border:1px solid rgba(30, 144, 255, 0.6);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked:hover {\n"
"	background: rgba(30, 144, 255, 0.5);\n"
"	border:1px solid rgba(30, 144, 255, 0.7);\n"
"}\n"
"\n"
"")
        self.viewStoreCheck.setChecked(True)

        self.horizontalLayout_2.addWidget(self.viewStoreCheck)

        self.viewSoundCheck = QCheckBox(self.layoutWidget1)
        self.viewSoundCheck.setObjectName("viewSoundCheck")
        self.viewSoundCheck.setMaximumSize(QSize(28, 16777215))
        self.viewSoundCheck.setStyleSheet("QCheckBox::indicator {\n"
"    image: url(:/images/icons/k1/sound.png);\n"
"	border: 1px solid rgba(30, 144, 255, 0.0);\n"
"	width: 26px;\n"
"	height: 26px;\n"
"}\n"
"\n"
"QCheckBox::indicator:unchecked:hover {\n"
"	background: rgba(30, 144, 255, 0.2);\n"
"	border: 1px solid rgba(30, 144, 255, 0.4);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked {\n"
"	background: rgba(30, 144, 255, 0.4);\n"
"	border:1px solid rgba(30, 144, 255, 0.6);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked:hover {\n"
"	background: rgba(30, 144, 255, 0.5);\n"
"	border:1px solid rgba(30, 144, 255, 0.7);\n"
"}\n"
"\n"
"")
        self.viewSoundCheck.setChecked(True)

        self.horizontalLayout_2.addWidget(self.viewSoundCheck)

        self.viewWaypointCheck = QCheckBox(self.layoutWidget1)
        self.viewWaypointCheck.setObjectName("viewWaypointCheck")
        self.viewWaypointCheck.setMaximumSize(QSize(28, 16777215))
        self.viewWaypointCheck.setStyleSheet("QCheckBox::indicator {\n"
"    image: url(:/images/icons/k1/waypoint.png);\n"
"	border: 1px solid rgba(30, 144, 255, 0.0);\n"
"	width: 26px;\n"
"	height: 26px;\n"
"}\n"
"\n"
"QCheckBox::indicator:unchecked:hover {\n"
"	background: rgba(30, 144, 255, 0.2);\n"
"	border: 1px solid rgba(30, 144, 255, 0.4);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked {\n"
"	background: rgba(30, 144, 255, 0.4);\n"
"	border:1px solid rgba(30, 144, 255, 0.6);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked:hover {\n"
"	background: rgba(30, 144, 255, 0.5);\n"
"	border:1px solid rgba(30, 144, 255, 0.7);\n"
"}\n"
"\n"
"")
        self.viewWaypointCheck.setChecked(True)

        self.horizontalLayout_2.addWidget(self.viewWaypointCheck)

        self.viewCameraCheck = QCheckBox(self.layoutWidget1)
        self.viewCameraCheck.setObjectName("viewCameraCheck")
        self.viewCameraCheck.setMaximumSize(QSize(28, 16777215))
        self.viewCameraCheck.setStyleSheet("QCheckBox::indicator {\n"
"    image: url(:/images/icons/k1/camera.png);\n"
"	border: 1px solid rgba(30, 144, 255, 0.0);\n"
"	width: 26px;\n"
"	height: 26px;\n"
"}\n"
"\n"
"QCheckBox::indicator:unchecked:hover {\n"
"	background: rgba(30, 144, 255, 0.2);\n"
"	border: 1px solid rgba(30, 144, 255, 0.4);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked {\n"
"	background: rgba(30, 144, 255, 0.4);\n"
"	border:1px solid rgba(30, 144, 255, 0.6);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked:hover {\n"
"	background: rgba(30, 144, 255, 0.5);\n"
"	border:1px solid rgba(30, 144, 255, 0.7);\n"
"}\n"
"\n"
"")
        self.viewCameraCheck.setChecked(True)

        self.horizontalLayout_2.addWidget(self.viewCameraCheck)

        self.viewEncounterCheck = QCheckBox(self.layoutWidget1)
        self.viewEncounterCheck.setObjectName("viewEncounterCheck")
        self.viewEncounterCheck.setMaximumSize(QSize(28, 16777215))
        self.viewEncounterCheck.setStyleSheet("QCheckBox::indicator {\n"
"    image: url(:/images/icons/k1/encounter.png);\n"
"	border: 1px solid rgba(30, 144, 255, 0.0);\n"
"	width: 26px;\n"
"	height: 26px;\n"
"}\n"
"\n"
"QCheckBox::indicator:unchecked:hover {\n"
"	background: rgba(30, 144, 255, 0.2);\n"
"	border: 1px solid rgba(30, 144, 255, 0.4);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked {\n"
"	background: rgba(30, 144, 255, 0.4);\n"
"	border:1px solid rgba(30, 144, 255, 0.6);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked:hover {\n"
"	background: rgba(30, 144, 255, 0.5);\n"
"	border:1px solid rgba(30, 144, 255, 0.7);\n"
"}\n"
"\n"
"")
        self.viewEncounterCheck.setChecked(True)

        self.horizontalLayout_2.addWidget(self.viewEncounterCheck)

        self.viewTriggerCheck = QCheckBox(self.layoutWidget1)
        self.viewTriggerCheck.setObjectName("viewTriggerCheck")
        self.viewTriggerCheck.setMaximumSize(QSize(28, 16777215))
        self.viewTriggerCheck.setStyleSheet("QCheckBox::indicator {\n"
"    image: url(:/images/icons/k1/trigger.png);\n"
"	border: 1px solid rgba(30, 144, 255, 0.0);\n"
"	width: 26px;\n"
"	height: 26px;\n"
"}\n"
"\n"
"QCheckBox::indicator:unchecked:hover {\n"
"	background: rgba(30, 144, 255, 0.2);\n"
"	border: 1px solid rgba(30, 144, 255, 0.4);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked {\n"
"	background: rgba(30, 144, 255, 0.4);\n"
"	border:1px solid rgba(30, 144, 255, 0.6);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked:hover {\n"
"	background: rgba(30, 144, 255, 0.5);\n"
"	border:1px solid rgba(30, 144, 255, 0.7);\n"
"}\n"
"\n"
"")
        self.viewTriggerCheck.setChecked(True)

        self.horizontalLayout_2.addWidget(self.viewTriggerCheck)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.renderArea = WalkmeshRenderer(self.layoutWidget1)
        self.renderArea.setObjectName("renderArea")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.renderArea.sizePolicy().hasHeightForWidth())
        self.renderArea.setSizePolicy(sizePolicy)
        self.renderArea.setMouseTracking(True)
        self.renderArea.setFocusPolicy(Qt.StrongFocus)
        self.renderArea.setContextMenuPolicy(Qt.CustomContextMenu)
        self.renderArea.setStyleSheet("background: black;")

        self.verticalLayout_2.addWidget(self.renderArea)

        self.splitter.addWidget(self.layoutWidget1)

        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 838, 22))
        self.menuNew = QMenu(self.menubar)
        self.menuNew.setObjectName("menuNew")
        self.menuView = QMenu(self.menubar)
        self.menuView.setObjectName("menuView")
        self.menuWaypointLabels = QMenu(self.menuView)
        self.menuWaypointLabels.setObjectName("menuWaypointLabels")
        self.menuTriggerLabels = QMenu(self.menuView)
        self.menuTriggerLabels.setObjectName("menuTriggerLabels")
        self.menuDoorLabels = QMenu(self.menuView)
        self.menuDoorLabels.setObjectName("menuDoorLabels")
        self.menuCreatureLabels = QMenu(self.menuView)
        self.menuCreatureLabels.setObjectName("menuCreatureLabels")
        self.menuPlaceableLabels = QMenu(self.menuView)
        self.menuPlaceableLabels.setObjectName("menuPlaceableLabels")
        self.menuMerchantLabels = QMenu(self.menuView)
        self.menuMerchantLabels.setObjectName("menuMerchantLabels")
        self.menuSound_Labels = QMenu(self.menuView)
        self.menuSound_Labels.setObjectName("menuSound_Labels")
        self.menuEncounterLabels = QMenu(self.menuView)
        self.menuEncounterLabels.setObjectName("menuEncounterLabels")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuNew.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menuNew.addAction(self.actionNew)
        self.menuNew.addAction(self.actionOpen)
        self.menuNew.addAction(self.actionSave)
        self.menuNew.addAction(self.actionSave_As)
        self.menuNew.addAction(self.actionRevert)
        self.menuNew.addSeparator()
        self.menuNew.addAction(self.actionUndo)
        self.menuNew.addAction(self.actionRedo)
        self.menuNew.addSeparator()
        self.menuNew.addAction(self.actionExit)
        self.menuView.addAction(self.actionZoomIn)
        self.menuView.addAction(self.actionZoomOut)
        self.menuView.addAction(self.actionRecentreCamera)
        self.menuView.addSeparator()
        self.menuView.addAction(self.menuCreatureLabels.menuAction())
        self.menuView.addAction(self.menuDoorLabels.menuAction())
        self.menuView.addAction(self.menuPlaceableLabels.menuAction())
        self.menuView.addAction(self.menuMerchantLabels.menuAction())
        self.menuView.addAction(self.menuSound_Labels.menuAction())
        self.menuView.addAction(self.menuWaypointLabels.menuAction())
        self.menuView.addAction(self.menuEncounterLabels.menuAction())
        self.menuView.addAction(self.menuTriggerLabels.menuAction())
        self.menuWaypointLabels.addAction(self.actionUseWaypointResRef)
        self.menuWaypointLabels.addAction(self.actionUseWaypointName)
        self.menuWaypointLabels.addAction(self.actionUseWaypointTag)
        self.menuTriggerLabels.addAction(self.actionUseTriggerResRef)
        self.menuTriggerLabels.addAction(self.actionUseTriggerName)
        self.menuTriggerLabels.addAction(self.actionUseTriggerTag)
        self.menuDoorLabels.addAction(self.actionUseDoorResRef)
        self.menuDoorLabels.addAction(self.actionUseDoorName)
        self.menuDoorLabels.addAction(self.actionUseDoorTag)
        self.menuCreatureLabels.addAction(self.actionUseCreatureResRef)
        self.menuCreatureLabels.addAction(self.actionUseCreatureName)
        self.menuCreatureLabels.addAction(self.actionUseCreatureTag)
        self.menuPlaceableLabels.addAction(self.actionUsePlaceableResRef)
        self.menuPlaceableLabels.addAction(self.actionUsePlaceableName)
        self.menuPlaceableLabels.addAction(self.actionUsePlaceableTag)
        self.menuMerchantLabels.addAction(self.actionUseMerchantResRef)
        self.menuMerchantLabels.addAction(self.actionUseMerchantName)
        self.menuMerchantLabels.addAction(self.actionUseMerchantTag)
        self.menuSound_Labels.addAction(self.actionUseSoundResRef)
        self.menuSound_Labels.addAction(self.actionUseSoundName)
        self.menuSound_Labels.addAction(self.actionUseSoundTag)
        self.menuEncounterLabels.addAction(self.actionUseEncounterResRef)
        self.menuEncounterLabels.addAction(self.actionUseEncounterName)
        self.menuEncounterLabels.addAction(self.actionUseEncounterTag)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", "MainWindow", None))
        self.actionUndo.setText(QCoreApplication.translate("MainWindow", "Undo", None))
#if QT_CONFIG(shortcut)
        self.actionUndo.setShortcut(QCoreApplication.translate("MainWindow", "Ctrl+Z", None))
#endif // QT_CONFIG(shortcut)
        self.actionRedo.setText(QCoreApplication.translate("MainWindow", "Redo", None))
#if QT_CONFIG(shortcut)
        self.actionRedo.setShortcut(QCoreApplication.translate("MainWindow", "Ctrl+Y", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(shortcut)
        self.actionRedo.setShortcut(QCoreApplication.translate("MainWindow", "Ctrl+Shift+Z", None))
#endif // QT_CONFIG(shortcut)
        self.actionNew.setText(QCoreApplication.translate("MainWindow", "New", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", "Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", "Save", None))
        self.actionSave_As.setText(QCoreApplication.translate("MainWindow", "Save As", None))
        self.actionRevert.setText(QCoreApplication.translate("MainWindow", "Revert", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", "Exit", None))
        self.actionZoomIn.setText(QCoreApplication.translate("MainWindow", "Zoom In", None))
        self.actionZoomOut.setText(QCoreApplication.translate("MainWindow", "Zoom Out", None))
        self.actionRecentreCamera.setText(QCoreApplication.translate("MainWindow", "Reset Camera", None))
        self.actionDeleteSelected.setText(QCoreApplication.translate("MainWindow", "Delete Selected", None))
        self.actionUseWaypointResRef.setText(QCoreApplication.translate("MainWindow", "ResRef", None))
        self.actionUseWaypointName.setText(QCoreApplication.translate("MainWindow", "Name", None))
        self.actionUseWaypointTag.setText(QCoreApplication.translate("MainWindow", "Tag", None))
        self.actionUseTriggerResRef.setText(QCoreApplication.translate("MainWindow", "ResRef", None))
        self.actionUseTriggerTag.setText(QCoreApplication.translate("MainWindow", "Tag", None))
        self.actionUseDoorResRef.setText(QCoreApplication.translate("MainWindow", "ResRef", None))
        self.actionUseDoorTag.setText(QCoreApplication.translate("MainWindow", "Tag", None))
        self.actionUseCreatureResRef.setText(QCoreApplication.translate("MainWindow", "ResRef", None))
        self.actionUseCreatureName.setText(QCoreApplication.translate("MainWindow", "Name", None))
        self.actionUseCreatureTag.setText(QCoreApplication.translate("MainWindow", "Tag", None))
        self.actionUseDoorName.setText(QCoreApplication.translate("MainWindow", "Name", None))
        self.actionUseDoorResTag.setText(QCoreApplication.translate("MainWindow", "Tag (UTD)", None))
        self.actionUseWaypointResName.setText(QCoreApplication.translate("MainWindow", "Name (UTW)", None))
        self.actionUseWaypointResTag.setText(QCoreApplication.translate("MainWindow", "Tag (UTW)", None))
        self.actionUseTriggerName.setText(QCoreApplication.translate("MainWindow", "Name", None))
        self.actionUseTriggerResTag.setText(QCoreApplication.translate("MainWindow", "Tag (UTT)", None))
        self.actionUsePlaceableResRef.setText(QCoreApplication.translate("MainWindow", "ResRef", None))
        self.actionUsePlaceableTag.setText(QCoreApplication.translate("MainWindow", "Tag", None))
        self.actionUsePlaceableName.setText(QCoreApplication.translate("MainWindow", "Name", None))
        self.actionUseMerchantResRef.setText(QCoreApplication.translate("MainWindow", "ResRef", None))
        self.actionUseMerchantName.setText(QCoreApplication.translate("MainWindow", "Name", None))
        self.actionUseMerchantTag.setText(QCoreApplication.translate("MainWindow", "Tag", None))
        self.actionUseSoundResRef.setText(QCoreApplication.translate("MainWindow", "ResRef", None))
        self.actionUseSoundName.setText(QCoreApplication.translate("MainWindow", "Name", None))
        self.actionUseSoundTag.setText(QCoreApplication.translate("MainWindow", "Tag", None))
        self.actionUseEncounterResRef.setText(QCoreApplication.translate("MainWindow", "ResRef", None))
        self.actionUseEncounterName.setText(QCoreApplication.translate("MainWindow", "Name", None))
        self.actionUseEncounterTag.setText(QCoreApplication.translate("MainWindow", "Tag", None))
        self.filterEdit.setText("")
        self.filterEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", "filter...", None))
#if QT_CONFIG(tooltip)
        self.lockInstancesCheck.setToolTip(QCoreApplication.translate("MainWindow", "Lock all instances in place", None))
#endif // QT_CONFIG(tooltip)
        self.lockInstancesCheck.setText("")
        self.label.setText(QCoreApplication.translate("MainWindow", "|", None))
#if QT_CONFIG(tooltip)
        self.viewCreatureCheck.setToolTip(QCoreApplication.translate("MainWindow", "Show Creatures", None))
#endif // QT_CONFIG(tooltip)
        self.viewCreatureCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewDoorCheck.setToolTip(QCoreApplication.translate("MainWindow", "Show Doors", None))
#endif // QT_CONFIG(tooltip)
        self.viewDoorCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewPlaceableCheck.setToolTip(QCoreApplication.translate("MainWindow", "Show Placeables", None))
#endif // QT_CONFIG(tooltip)
        self.viewPlaceableCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewStoreCheck.setToolTip(QCoreApplication.translate("MainWindow", "Show Merchants", None))
#endif // QT_CONFIG(tooltip)
        self.viewStoreCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewSoundCheck.setToolTip(QCoreApplication.translate("MainWindow", "Show Sounds", None))
#endif // QT_CONFIG(tooltip)
        self.viewSoundCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewWaypointCheck.setToolTip(QCoreApplication.translate("MainWindow", "Show Waypoints", None))
#endif // QT_CONFIG(tooltip)
        self.viewWaypointCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewCameraCheck.setToolTip(QCoreApplication.translate("MainWindow", "Show Cameras", None))
#endif // QT_CONFIG(tooltip)
        self.viewCameraCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewEncounterCheck.setToolTip(QCoreApplication.translate("MainWindow", "Show Encounters", None))
#endif // QT_CONFIG(tooltip)
        self.viewEncounterCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewTriggerCheck.setToolTip(QCoreApplication.translate("MainWindow", "Show Triggers", None))
#endif // QT_CONFIG(tooltip)
        self.viewTriggerCheck.setText("")
        self.menuNew.setTitle(QCoreApplication.translate("MainWindow", "File", None))
        self.menuView.setTitle(QCoreApplication.translate("MainWindow", "View", None))
        self.menuWaypointLabels.setTitle(QCoreApplication.translate("MainWindow", "Waypoint Labels", None))
        self.menuTriggerLabels.setTitle(QCoreApplication.translate("MainWindow", "Trigger Labels", None))
        self.menuDoorLabels.setTitle(QCoreApplication.translate("MainWindow", "Door Labels", None))
        self.menuCreatureLabels.setTitle(QCoreApplication.translate("MainWindow", "Creature Labels", None))
        self.menuPlaceableLabels.setTitle(QCoreApplication.translate("MainWindow", "Placeable Labels", None))
        self.menuMerchantLabels.setTitle(QCoreApplication.translate("MainWindow", "Merchant Labels", None))
        self.menuSound_Labels.setTitle(QCoreApplication.translate("MainWindow", "Sound Labels", None))
        self.menuEncounterLabels.setTitle(QCoreApplication.translate("MainWindow", "Encounter Labels", None))
    # retranslateUi

