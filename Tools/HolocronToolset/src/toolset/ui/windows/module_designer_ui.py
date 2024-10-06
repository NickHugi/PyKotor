
################################################################################
## Form generated from reading UI file 'module_designer.ui'
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
    QFrame,
    QHBoxLayout,
    QListWidget,
    QMenu,
    QMenuBar,
    QSizePolicy,
    QSpacerItem,
    QSplitter,
    QStatusBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from toolset.gui.widgets.renderer.module import ModuleRenderer
from toolset.gui.widgets.renderer.walkmesh import WalkmeshRenderer


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(970, 651)
        MainWindow.setFocusPolicy(Qt.StrongFocus)
        self.actionUndo = QAction(MainWindow)
        self.actionUndo.setObjectName("actionUndo")
        self.actionRedo = QAction(MainWindow)
        self.actionRedo.setObjectName("actionRedo")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.actiona = QAction(MainWindow)
        self.actiona.setObjectName("actiona")
        self.actionInstructions = QAction(MainWindow)
        self.actionInstructions.setObjectName("actionInstructions")
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionHide3DView = QAction(MainWindow)
        self.actionHide3DView.setObjectName("actionHide3DView")
        self.actionHide2DView = QAction(MainWindow)
        self.actionHide2DView.setObjectName("actionHide2DView")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(4)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.lockInstancesCheck = QCheckBox(self.centralwidget)
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

        self.line_2 = QFrame(self.centralwidget)
        self.line_2.setObjectName("line_2")
        self.line_2.setFrameShape(QFrame.VLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_2.addWidget(self.line_2)

        self.cursorCheck = QCheckBox(self.centralwidget)
        self.cursorCheck.setObjectName("cursorCheck")
        self.cursorCheck.setMaximumSize(QSize(28, 16777215))
        self.cursorCheck.setStyleSheet("QCheckbox {\n"
"	spacing: 0px;\n"
"}\n"
"\n"
"QCheckBox::indicator {\n"
"    image: url(:/images/icons/cursor.png);\n"
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
        self.cursorCheck.setChecked(True)

        self.horizontalLayout_2.addWidget(self.cursorCheck)

        self.backfaceCheck = QCheckBox(self.centralwidget)
        self.backfaceCheck.setObjectName("backfaceCheck")
        self.backfaceCheck.setMaximumSize(QSize(28, 16777215))
        self.backfaceCheck.setStyleSheet("QCheckbox {\n"
"	spacing: 0px;\n"
"}\n"
"\n"
"QCheckBox::indicator {\n"
"    image: url(:/images/icons/backface.png);\n"
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
        self.backfaceCheck.setChecked(True)

        self.horizontalLayout_2.addWidget(self.backfaceCheck)

        self.lightmapCheck = QCheckBox(self.centralwidget)
        self.lightmapCheck.setObjectName("lightmapCheck")
        self.lightmapCheck.setMaximumSize(QSize(28, 16777215))
        self.lightmapCheck.setStyleSheet("QCheckbox {\n"
"	spacing: 0px;\n"
"}\n"
"\n"
"QCheckBox::indicator {\n"
"    image: url(:/images/icons/lightmap.png);\n"
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
        self.lightmapCheck.setChecked(True)

        self.horizontalLayout_2.addWidget(self.lightmapCheck)

        self.line = QFrame(self.centralwidget)
        self.line.setObjectName("line")
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_2.addWidget(self.line)

        self.viewCreatureCheck = QCheckBox(self.centralwidget)
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

        self.viewDoorCheck = QCheckBox(self.centralwidget)
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

        self.viewPlaceableCheck = QCheckBox(self.centralwidget)
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

        self.viewStoreCheck = QCheckBox(self.centralwidget)
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

        self.viewSoundCheck = QCheckBox(self.centralwidget)
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

        self.viewWaypointCheck = QCheckBox(self.centralwidget)
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

        self.viewCameraCheck = QCheckBox(self.centralwidget)
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

        self.viewEncounterCheck = QCheckBox(self.centralwidget)
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

        self.viewTriggerCheck = QCheckBox(self.centralwidget)
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


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.resourceTree = QTreeWidget(self.centralwidget)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, "1");
        self.resourceTree.setHeaderItem(__qtreewidgetitem)
        self.resourceTree.setObjectName("resourceTree")
        self.resourceTree.setMaximumSize(QSize(200, 16777215))
        self.resourceTree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.resourceTree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.resourceTree.setHeaderHidden(True)

        self.horizontalLayout.addWidget(self.resourceTree)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.splitter = QSplitter(self.centralwidget)
        self.splitter.setObjectName("splitter")
        self.splitter.setOrientation(Qt.Vertical)
        self.mainRenderer = ModuleRenderer(self.splitter)
        self.mainRenderer.setObjectName("mainRenderer")
        self.mainRenderer.setMouseTracking(True)
        self.splitter.addWidget(self.mainRenderer)
        self.flatRenderer = WalkmeshRenderer(self.splitter)
        self.flatRenderer.setObjectName("flatRenderer")
        self.flatRenderer.setMouseTracking(True)
        self.splitter.addWidget(self.flatRenderer)

        self.verticalLayout_2.addWidget(self.splitter)


        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.instanceList = QListWidget(self.centralwidget)
        self.instanceList.setObjectName("instanceList")
        self.instanceList.setMaximumSize(QSize(200, 16777215))
        self.instanceList.setContextMenuPolicy(Qt.CustomContextMenu)

        self.horizontalLayout.addWidget(self.instanceList)


        self.verticalLayout.addLayout(self.horizontalLayout)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 970, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionUndo)
        self.menuFile.addAction(self.actionRedo)
        self.menuHelp.addAction(self.actionInstructions)

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
        self.actionSave.setText(QCoreApplication.translate("MainWindow", "Save GIT", None))
        self.actiona.setText(QCoreApplication.translate("MainWindow", "Placeholdewr", None))
        self.actionInstructions.setText(QCoreApplication.translate("MainWindow", "Instructions", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", "Open", None))
        self.actionHide3DView.setText(QCoreApplication.translate("MainWindow", "Hide 3D View", None))
        self.actionHide2DView.setText(QCoreApplication.translate("MainWindow", "Hide 2D View", None))
#if QT_CONFIG(tooltip)
        self.lockInstancesCheck.setToolTip(QCoreApplication.translate("MainWindow", "Lock all instances in place", None))
#endif // QT_CONFIG(tooltip)
        self.lockInstancesCheck.setText("")
#if QT_CONFIG(tooltip)
        self.cursorCheck.setToolTip(QCoreApplication.translate("MainWindow", "Display cursor at mouse", None))
#endif // QT_CONFIG(tooltip)
        self.cursorCheck.setText("")
#if QT_CONFIG(tooltip)
        self.backfaceCheck.setToolTip(QCoreApplication.translate("MainWindow", "Enable backface culling", None))
#endif // QT_CONFIG(tooltip)
        self.backfaceCheck.setText("")
#if QT_CONFIG(tooltip)
        self.lightmapCheck.setToolTip(QCoreApplication.translate("MainWindow", "Enable lightmaps", None))
#endif // QT_CONFIG(tooltip)
        self.lightmapCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewCreatureCheck.setToolTip(QCoreApplication.translate("MainWindow", "Creatures", None))
#endif // QT_CONFIG(tooltip)
        self.viewCreatureCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewDoorCheck.setToolTip(QCoreApplication.translate("MainWindow", "Doors", None))
#endif // QT_CONFIG(tooltip)
        self.viewDoorCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewPlaceableCheck.setToolTip(QCoreApplication.translate("MainWindow", "Placeables", None))
#endif // QT_CONFIG(tooltip)
        self.viewPlaceableCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewStoreCheck.setToolTip(QCoreApplication.translate("MainWindow", "Merchants", None))
#endif // QT_CONFIG(tooltip)
        self.viewStoreCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewSoundCheck.setToolTip(QCoreApplication.translate("MainWindow", "Sounds", None))
#endif // QT_CONFIG(tooltip)
        self.viewSoundCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewWaypointCheck.setToolTip(QCoreApplication.translate("MainWindow", "Waypoints", None))
#endif // QT_CONFIG(tooltip)
        self.viewWaypointCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewCameraCheck.setToolTip(QCoreApplication.translate("MainWindow", "Cameras", None))
#endif // QT_CONFIG(tooltip)
        self.viewCameraCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewEncounterCheck.setToolTip(QCoreApplication.translate("MainWindow", "Encounters", None))
#endif // QT_CONFIG(tooltip)
        self.viewEncounterCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewTriggerCheck.setToolTip(QCoreApplication.translate("MainWindow", "Triggers", None))
#endif // QT_CONFIG(tooltip)
        self.viewTriggerCheck.setText("")
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", "File", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", "Help", None))
    # retranslateUi

