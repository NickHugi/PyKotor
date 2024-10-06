
################################################################################
## Form generated from reading UI file 'lyt.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, Qt
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QGraphicsView, QGroupBox, QHBoxLayout, QListWidget, QPushButton, QSlider, QSplitter, QTabWidget, QVBoxLayout, QWidget


class Ui_LYTEditor:
    def setupUi(self, LYTEditor):
        if not LYTEditor.objectName():
            LYTEditor.setObjectName("LYTEditor")
        LYTEditor.resize(1200, 800)
        self.horizontalLayout = QHBoxLayout(LYTEditor)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.splitter = QSplitter(LYTEditor)
        self.splitter.setObjectName("splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.leftWidget = QWidget(self.splitter)
        self.leftWidget.setObjectName("leftWidget")
        self.verticalLayout = QVBoxLayout(self.leftWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.viewTabWidget = QTabWidget(self.leftWidget)
        self.viewTabWidget.setObjectName("viewTabWidget")
        self.topDownTab = QWidget()
        self.topDownTab.setObjectName("topDownTab")
        self.verticalLayout_7 = QVBoxLayout(self.topDownTab)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.graphicsView = QGraphicsView(self.topDownTab)
        self.graphicsView.setObjectName("graphicsView")
        self.graphicsView.setDragMode(QGraphicsView.ScrollHandDrag)

        self.verticalLayout_7.addWidget(self.graphicsView)

        self.viewTabWidget.addTab(self.topDownTab, "")
        self.threeDTab = QWidget()
        self.threeDTab.setObjectName("threeDTab")
        self.verticalLayout_8 = QVBoxLayout(self.threeDTab)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.openGLWidget = QOpenGLWidget(self.threeDTab)
        self.openGLWidget.setObjectName("openGLWidget")

        self.verticalLayout_8.addWidget(self.openGLWidget)

        self.viewTabWidget.addTab(self.threeDTab, "")

        self.verticalLayout.addWidget(self.viewTabWidget)

        self.zoomSlider = QSlider(self.leftWidget)
        self.zoomSlider.setObjectName("zoomSlider")
        self.zoomSlider.setMinimum(10)
        self.zoomSlider.setMaximum(200)
        self.zoomSlider.setValue(100)
        self.zoomSlider.setOrientation(Qt.Horizontal)

        self.verticalLayout.addWidget(self.zoomSlider)

        self.splitter.addWidget(self.leftWidget)
        self.rightWidget = QWidget(self.splitter)
        self.rightWidget.setObjectName("rightWidget")
        self.verticalLayout_2 = QVBoxLayout(self.rightWidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.tabWidget = QTabWidget(self.rightWidget)
        self.tabWidget.setObjectName("tabWidget")
        self.roomsTab = QWidget()
        self.roomsTab.setObjectName("roomsTab")
        self.verticalLayout_3 = QVBoxLayout(self.roomsTab)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.roomsList = QListWidget(self.roomsTab)
        self.roomsList.setObjectName("roomsList")

        self.verticalLayout_3.addWidget(self.roomsList)

        self.addRoomButton = QPushButton(self.roomsTab)
        self.addRoomButton.setObjectName("addRoomButton")

        self.verticalLayout_3.addWidget(self.addRoomButton)

        self.tabWidget.addTab(self.roomsTab, "")
        self.tracksTab = QWidget()
        self.tracksTab.setObjectName("tracksTab")
        self.verticalLayout_4 = QVBoxLayout(self.tracksTab)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.tracksList = QListWidget(self.tracksTab)
        self.tracksList.setObjectName("tracksList")

        self.verticalLayout_4.addWidget(self.tracksList)

        self.addTrackButton = QPushButton(self.tracksTab)
        self.addTrackButton.setObjectName("addTrackButton")

        self.verticalLayout_4.addWidget(self.addTrackButton)

        self.tabWidget.addTab(self.tracksTab, "")
        self.obstaclesTab = QWidget()
        self.obstaclesTab.setObjectName("obstaclesTab")
        self.verticalLayout_5 = QVBoxLayout(self.obstaclesTab)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.obstaclesList = QListWidget(self.obstaclesTab)
        self.obstaclesList.setObjectName("obstaclesList")

        self.verticalLayout_5.addWidget(self.obstaclesList)

        self.addObstacleButton = QPushButton(self.obstaclesTab)
        self.addObstacleButton.setObjectName("addObstacleButton")

        self.verticalLayout_5.addWidget(self.addObstacleButton)

        self.tabWidget.addTab(self.obstaclesTab, "")
        self.doorhooksTab = QWidget()
        self.doorhooksTab.setObjectName("doorhooksTab")
        self.verticalLayout_6 = QVBoxLayout(self.doorhooksTab)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.doorhooksList = QListWidget(self.doorhooksTab)
        self.doorhooksList.setObjectName("doorhooksList")

        self.verticalLayout_6.addWidget(self.doorhooksList)

        self.addDoorHookButton = QPushButton(self.doorhooksTab)
        self.addDoorHookButton.setObjectName("addDoorHookButton")

        self.verticalLayout_6.addWidget(self.addDoorHookButton)

        self.tabWidget.addTab(self.doorhooksTab, "")

        self.verticalLayout_2.addWidget(self.tabWidget)

        self.texturesGroupBox = QGroupBox(self.rightWidget)
        self.texturesGroupBox.setObjectName("texturesGroupBox")
        self.verticalLayout_9 = QVBoxLayout(self.texturesGroupBox)
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.textureBrowser = QListWidget(self.texturesGroupBox)
        self.textureBrowser.setObjectName("textureBrowser")

        self.verticalLayout_9.addWidget(self.textureBrowser)

        self.importTextureButton = QPushButton(self.texturesGroupBox)
        self.importTextureButton.setObjectName("importTextureButton")

        self.verticalLayout_9.addWidget(self.importTextureButton)


        self.verticalLayout_2.addWidget(self.texturesGroupBox)

        self.roomTemplatesGroupBox = QGroupBox(self.rightWidget)
        self.roomTemplatesGroupBox.setObjectName("roomTemplatesGroupBox")
        self.verticalLayout_10 = QVBoxLayout(self.roomTemplatesGroupBox)
        self.verticalLayout_10.setObjectName("verticalLayout_10")
        self.roomTemplateList = QListWidget(self.roomTemplatesGroupBox)
        self.roomTemplateList.setObjectName("roomTemplateList")

        self.verticalLayout_10.addWidget(self.roomTemplateList)


        self.verticalLayout_2.addWidget(self.roomTemplatesGroupBox)

        self.importModelButton = QPushButton(self.rightWidget)
        self.importModelButton.setObjectName("importModelButton")

        self.verticalLayout_2.addWidget(self.importModelButton)

        self.generateWalkmeshButton = QPushButton(self.rightWidget)
        self.generateWalkmeshButton.setObjectName("generateWalkmeshButton")

        self.verticalLayout_2.addWidget(self.generateWalkmeshButton)

        self.splitter.addWidget(self.rightWidget)

        self.horizontalLayout.addWidget(self.splitter)


        self.retranslateUi(LYTEditor)

        QMetaObject.connectSlotsByName(LYTEditor)
    # setupUi

    def retranslateUi(self, LYTEditor):
        LYTEditor.setWindowTitle(QCoreApplication.translate("LYTEditor", "LYT Editor", None))
        self.viewTabWidget.setTabText(self.viewTabWidget.indexOf(self.topDownTab), QCoreApplication.translate("LYTEditor", "Top-Down View", None))
        self.viewTabWidget.setTabText(self.viewTabWidget.indexOf(self.threeDTab), QCoreApplication.translate("LYTEditor", "3D View", None))
        self.addRoomButton.setText(QCoreApplication.translate("LYTEditor", "Add Room", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.roomsTab), QCoreApplication.translate("LYTEditor", "Rooms", None))
        self.addTrackButton.setText(QCoreApplication.translate("LYTEditor", "Add Track", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tracksTab), QCoreApplication.translate("LYTEditor", "Tracks", None))
        self.addObstacleButton.setText(QCoreApplication.translate("LYTEditor", "Add Obstacle", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.obstaclesTab), QCoreApplication.translate("LYTEditor", "Obstacles", None))
        self.addDoorHookButton.setText(QCoreApplication.translate("LYTEditor", "Add Door Hook", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.doorhooksTab), QCoreApplication.translate("LYTEditor", "Doorhooks", None))
        self.texturesGroupBox.setTitle(QCoreApplication.translate("LYTEditor", "Textures", None))
        self.importTextureButton.setText(QCoreApplication.translate("LYTEditor", "Import Texture", None))
        self.roomTemplatesGroupBox.setTitle(QCoreApplication.translate("LYTEditor", "Room Templates", None))
        self.importModelButton.setText(QCoreApplication.translate("LYTEditor", "Import Model", None))
        self.generateWalkmeshButton.setText(QCoreApplication.translate("LYTEditor", "Generate Walkmesh", None))
    # retranslateUi

