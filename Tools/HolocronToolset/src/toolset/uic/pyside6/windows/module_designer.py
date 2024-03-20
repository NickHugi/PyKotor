# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'module_designer.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QFrame,
    QHBoxLayout, QHeaderView, QListWidget, QListWidgetItem,
    QMainWindow, QMenu, QMenuBar, QSizePolicy,
    QSpacerItem, QSplitter, QStatusBar, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget)

from toolset.gui.widgets.renderer.module import ModuleRenderer
from toolset.gui.widgets.renderer.walkmesh import WalkmeshRenderer
from toolset.rcc import resources_rc_pyside6
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(970, 651)
        MainWindow.setFocusPolicy(Qt.StrongFocus)
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actiona = QAction(MainWindow)
        self.actiona.setObjectName(u"actiona")
        self.actionInstructions = QAction(MainWindow)
        self.actionInstructions.setObjectName(u"actionInstructions")
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName(u"actionOpen")
        self.actionHide3DView = QAction(MainWindow)
        self.actionHide3DView.setObjectName(u"actionHide3DView")
        self.actionHide2DView = QAction(MainWindow)
        self.actionHide2DView.setObjectName(u"actionHide2DView")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(4)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.lockInstancesCheck = QCheckBox(self.centralwidget)
        self.lockInstancesCheck.setObjectName(u"lockInstancesCheck")
        self.lockInstancesCheck.setMaximumSize(QSize(28, 16777215))
        self.lockInstancesCheck.setStyleSheet(u"QCheckbox {\n"
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
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.VLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_2.addWidget(self.line_2)

        self.cursorCheck = QCheckBox(self.centralwidget)
        self.cursorCheck.setObjectName(u"cursorCheck")
        self.cursorCheck.setMaximumSize(QSize(28, 16777215))
        self.cursorCheck.setStyleSheet(u"QCheckbox {\n"
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
        self.backfaceCheck.setObjectName(u"backfaceCheck")
        self.backfaceCheck.setMaximumSize(QSize(28, 16777215))
        self.backfaceCheck.setStyleSheet(u"QCheckbox {\n"
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
        self.lightmapCheck.setObjectName(u"lightmapCheck")
        self.lightmapCheck.setMaximumSize(QSize(28, 16777215))
        self.lightmapCheck.setStyleSheet(u"QCheckbox {\n"
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
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_2.addWidget(self.line)

        self.viewCreatureCheck = QCheckBox(self.centralwidget)
        self.viewCreatureCheck.setObjectName(u"viewCreatureCheck")
        self.viewCreatureCheck.setMaximumSize(QSize(28, 16777215))
        self.viewCreatureCheck.setStyleSheet(u"QCheckbox {\n"
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
        self.viewDoorCheck.setObjectName(u"viewDoorCheck")
        self.viewDoorCheck.setMaximumSize(QSize(28, 16777215))
        self.viewDoorCheck.setStyleSheet(u"QCheckBox::indicator {\n"
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
        self.viewPlaceableCheck.setObjectName(u"viewPlaceableCheck")
        self.viewPlaceableCheck.setMaximumSize(QSize(28, 16777215))
        self.viewPlaceableCheck.setStyleSheet(u"QCheckBox::indicator {\n"
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
        self.viewStoreCheck.setObjectName(u"viewStoreCheck")
        self.viewStoreCheck.setMaximumSize(QSize(28, 16777215))
        self.viewStoreCheck.setStyleSheet(u"QCheckBox::indicator {\n"
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
        self.viewSoundCheck.setObjectName(u"viewSoundCheck")
        self.viewSoundCheck.setMaximumSize(QSize(28, 16777215))
        self.viewSoundCheck.setStyleSheet(u"QCheckBox::indicator {\n"
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
        self.viewWaypointCheck.setObjectName(u"viewWaypointCheck")
        self.viewWaypointCheck.setMaximumSize(QSize(28, 16777215))
        self.viewWaypointCheck.setStyleSheet(u"QCheckBox::indicator {\n"
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
        self.viewCameraCheck.setObjectName(u"viewCameraCheck")
        self.viewCameraCheck.setMaximumSize(QSize(28, 16777215))
        self.viewCameraCheck.setStyleSheet(u"QCheckBox::indicator {\n"
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
        self.viewEncounterCheck.setObjectName(u"viewEncounterCheck")
        self.viewEncounterCheck.setMaximumSize(QSize(28, 16777215))
        self.viewEncounterCheck.setStyleSheet(u"QCheckBox::indicator {\n"
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
        self.viewTriggerCheck.setObjectName(u"viewTriggerCheck")
        self.viewTriggerCheck.setMaximumSize(QSize(28, 16777215))
        self.viewTriggerCheck.setStyleSheet(u"QCheckBox::indicator {\n"
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
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.resourceTree = QTreeWidget(self.centralwidget)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"1");
        self.resourceTree.setHeaderItem(__qtreewidgetitem)
        self.resourceTree.setObjectName(u"resourceTree")
        self.resourceTree.setMaximumSize(QSize(200, 16777215))
        self.resourceTree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.resourceTree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.resourceTree.setHeaderHidden(True)

        self.horizontalLayout.addWidget(self.resourceTree)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.splitter = QSplitter(self.centralwidget)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Vertical)
        self.mainRenderer = ModuleRenderer(self.splitter)
        self.mainRenderer.setObjectName(u"mainRenderer")
        self.mainRenderer.setMouseTracking(True)
        self.splitter.addWidget(self.mainRenderer)
        self.flatRenderer = WalkmeshRenderer(self.splitter)
        self.flatRenderer.setObjectName(u"flatRenderer")
        self.flatRenderer.setMouseTracking(True)
        self.splitter.addWidget(self.flatRenderer)

        self.verticalLayout_2.addWidget(self.splitter)


        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.instanceList = QListWidget(self.centralwidget)
        self.instanceList.setObjectName(u"instanceList")
        self.instanceList.setMaximumSize(QSize(200, 16777215))
        self.instanceList.setContextMenuPolicy(Qt.CustomContextMenu)

        self.horizontalLayout.addWidget(self.instanceList)


        self.verticalLayout.addLayout(self.horizontalLayout)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 970, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuHelp.addAction(self.actionInstructions)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save GIT", None))
        self.actiona.setText(QCoreApplication.translate("MainWindow", u"Placeholdewr", None))
        self.actionInstructions.setText(QCoreApplication.translate("MainWindow", u"Instructions", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", u"Open", None))
        self.actionHide3DView.setText(QCoreApplication.translate("MainWindow", u"Hide 3D View", None))
        self.actionHide2DView.setText(QCoreApplication.translate("MainWindow", u"Hide 2D View", None))
#if QT_CONFIG(tooltip)
        self.lockInstancesCheck.setToolTip(QCoreApplication.translate("MainWindow", u"Lock all instances in place", None))
#endif // QT_CONFIG(tooltip)
        self.lockInstancesCheck.setText("")
#if QT_CONFIG(tooltip)
        self.cursorCheck.setToolTip(QCoreApplication.translate("MainWindow", u"Display cursor at mouse", None))
#endif // QT_CONFIG(tooltip)
        self.cursorCheck.setText("")
#if QT_CONFIG(tooltip)
        self.backfaceCheck.setToolTip(QCoreApplication.translate("MainWindow", u"Enable backface culling", None))
#endif // QT_CONFIG(tooltip)
        self.backfaceCheck.setText("")
#if QT_CONFIG(tooltip)
        self.lightmapCheck.setToolTip(QCoreApplication.translate("MainWindow", u"Enable lightmaps", None))
#endif // QT_CONFIG(tooltip)
        self.lightmapCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewCreatureCheck.setToolTip(QCoreApplication.translate("MainWindow", u"Creatures", None))
#endif // QT_CONFIG(tooltip)
        self.viewCreatureCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewDoorCheck.setToolTip(QCoreApplication.translate("MainWindow", u"Doors", None))
#endif // QT_CONFIG(tooltip)
        self.viewDoorCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewPlaceableCheck.setToolTip(QCoreApplication.translate("MainWindow", u"Placeables", None))
#endif // QT_CONFIG(tooltip)
        self.viewPlaceableCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewStoreCheck.setToolTip(QCoreApplication.translate("MainWindow", u"Merchants", None))
#endif // QT_CONFIG(tooltip)
        self.viewStoreCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewSoundCheck.setToolTip(QCoreApplication.translate("MainWindow", u"Sounds", None))
#endif // QT_CONFIG(tooltip)
        self.viewSoundCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewWaypointCheck.setToolTip(QCoreApplication.translate("MainWindow", u"Waypoints", None))
#endif // QT_CONFIG(tooltip)
        self.viewWaypointCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewCameraCheck.setToolTip(QCoreApplication.translate("MainWindow", u"Cameras", None))
#endif // QT_CONFIG(tooltip)
        self.viewCameraCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewEncounterCheck.setToolTip(QCoreApplication.translate("MainWindow", u"Encounters", None))
#endif // QT_CONFIG(tooltip)
        self.viewEncounterCheck.setText("")
#if QT_CONFIG(tooltip)
        self.viewTriggerCheck.setToolTip(QCoreApplication.translate("MainWindow", u"Triggers", None))
#endif // QT_CONFIG(tooltip)
        self.viewTriggerCheck.setText("")
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
    # retranslateUi

