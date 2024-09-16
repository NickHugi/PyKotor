# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'lyt.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_LYTEditor(object):
    def setupUi(self, LYTEditor):
        if not LYTEditor.objectName():
            LYTEditor.setObjectName(u"LYTEditor")
        LYTEditor.resize(1200, 800)
        self.horizontalLayout = QHBoxLayout(LYTEditor)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.splitter = QSplitter(LYTEditor)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.leftWidget = QWidget(self.splitter)
        self.leftWidget.setObjectName(u"leftWidget")
        self.verticalLayout = QVBoxLayout(self.leftWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.viewTabWidget = QTabWidget(self.leftWidget)
        self.viewTabWidget.setObjectName(u"viewTabWidget")
        self.topDownTab = QWidget()
        self.topDownTab.setObjectName(u"topDownTab")
        self.verticalLayout_7 = QVBoxLayout(self.topDownTab)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.graphicsView = QGraphicsView(self.topDownTab)
        self.graphicsView.setObjectName(u"graphicsView")
        self.graphicsView.setDragMode(QGraphicsView.ScrollHandDrag)

        self.verticalLayout_7.addWidget(self.graphicsView)

        self.viewTabWidget.addTab(self.topDownTab, "")
        self.threeDTab = QWidget()
        self.threeDTab.setObjectName(u"threeDTab")
        self.verticalLayout_8 = QVBoxLayout(self.threeDTab)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.openGLWidget = QOpenGLWidget(self.threeDTab)
        self.openGLWidget.setObjectName(u"openGLWidget")

        self.verticalLayout_8.addWidget(self.openGLWidget)

        self.viewTabWidget.addTab(self.threeDTab, "")

        self.verticalLayout.addWidget(self.viewTabWidget)

        self.zoomSlider = QSlider(self.leftWidget)
        self.zoomSlider.setObjectName(u"zoomSlider")
        self.zoomSlider.setMinimum(10)
        self.zoomSlider.setMaximum(200)
        self.zoomSlider.setValue(100)
        self.zoomSlider.setOrientation(Qt.Horizontal)

        self.verticalLayout.addWidget(self.zoomSlider)

        self.splitter.addWidget(self.leftWidget)
        self.rightWidget = QWidget(self.splitter)
        self.rightWidget.setObjectName(u"rightWidget")
        self.verticalLayout_2 = QVBoxLayout(self.rightWidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.tabWidget = QTabWidget(self.rightWidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.roomsTab = QWidget()
        self.roomsTab.setObjectName(u"roomsTab")
        self.verticalLayout_3 = QVBoxLayout(self.roomsTab)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.roomsList = QListWidget(self.roomsTab)
        self.roomsList.setObjectName(u"roomsList")

        self.verticalLayout_3.addWidget(self.roomsList)

        self.addRoomButton = QPushButton(self.roomsTab)
        self.addRoomButton.setObjectName(u"addRoomButton")

        self.verticalLayout_3.addWidget(self.addRoomButton)

        self.tabWidget.addTab(self.roomsTab, "")
        self.tracksTab = QWidget()
        self.tracksTab.setObjectName(u"tracksTab")
        self.verticalLayout_4 = QVBoxLayout(self.tracksTab)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.tracksList = QListWidget(self.tracksTab)
        self.tracksList.setObjectName(u"tracksList")

        self.verticalLayout_4.addWidget(self.tracksList)

        self.addTrackButton = QPushButton(self.tracksTab)
        self.addTrackButton.setObjectName(u"addTrackButton")

        self.verticalLayout_4.addWidget(self.addTrackButton)

        self.tabWidget.addTab(self.tracksTab, "")
        self.obstaclesTab = QWidget()
        self.obstaclesTab.setObjectName(u"obstaclesTab")
        self.verticalLayout_5 = QVBoxLayout(self.obstaclesTab)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.obstaclesList = QListWidget(self.obstaclesTab)
        self.obstaclesList.setObjectName(u"obstaclesList")

        self.verticalLayout_5.addWidget(self.obstaclesList)

        self.addObstacleButton = QPushButton(self.obstaclesTab)
        self.addObstacleButton.setObjectName(u"addObstacleButton")

        self.verticalLayout_5.addWidget(self.addObstacleButton)

        self.tabWidget.addTab(self.obstaclesTab, "")
        self.doorhooksTab = QWidget()
        self.doorhooksTab.setObjectName(u"doorhooksTab")
        self.verticalLayout_6 = QVBoxLayout(self.doorhooksTab)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.doorhooksList = QListWidget(self.doorhooksTab)
        self.doorhooksList.setObjectName(u"doorhooksList")

        self.verticalLayout_6.addWidget(self.doorhooksList)

        self.addDoorHookButton = QPushButton(self.doorhooksTab)
        self.addDoorHookButton.setObjectName(u"addDoorHookButton")

        self.verticalLayout_6.addWidget(self.addDoorHookButton)

        self.tabWidget.addTab(self.doorhooksTab, "")

        self.verticalLayout_2.addWidget(self.tabWidget)

        self.texturesGroupBox = QGroupBox(self.rightWidget)
        self.texturesGroupBox.setObjectName(u"texturesGroupBox")
        self.verticalLayout_9 = QVBoxLayout(self.texturesGroupBox)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.textureBrowser = QListWidget(self.texturesGroupBox)
        self.textureBrowser.setObjectName(u"textureBrowser")

        self.verticalLayout_9.addWidget(self.textureBrowser)

        self.importTextureButton = QPushButton(self.texturesGroupBox)
        self.importTextureButton.setObjectName(u"importTextureButton")

        self.verticalLayout_9.addWidget(self.importTextureButton)


        self.verticalLayout_2.addWidget(self.texturesGroupBox)

        self.roomTemplatesGroupBox = QGroupBox(self.rightWidget)
        self.roomTemplatesGroupBox.setObjectName(u"roomTemplatesGroupBox")
        self.verticalLayout_10 = QVBoxLayout(self.roomTemplatesGroupBox)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.roomTemplateList = QListWidget(self.roomTemplatesGroupBox)
        self.roomTemplateList.setObjectName(u"roomTemplateList")

        self.verticalLayout_10.addWidget(self.roomTemplateList)


        self.verticalLayout_2.addWidget(self.roomTemplatesGroupBox)

        self.importModelButton = QPushButton(self.rightWidget)
        self.importModelButton.setObjectName(u"importModelButton")

        self.verticalLayout_2.addWidget(self.importModelButton)

        self.generateWalkmeshButton = QPushButton(self.rightWidget)
        self.generateWalkmeshButton.setObjectName(u"generateWalkmeshButton")

        self.verticalLayout_2.addWidget(self.generateWalkmeshButton)

        self.splitter.addWidget(self.rightWidget)

        self.horizontalLayout.addWidget(self.splitter)


        self.retranslateUi(LYTEditor)

        QMetaObject.connectSlotsByName(LYTEditor)
    # setupUi

    def retranslateUi(self, LYTEditor):
        LYTEditor.setWindowTitle(QCoreApplication.translate("LYTEditor", u"LYT Editor", None))
        self.viewTabWidget.setTabText(self.viewTabWidget.indexOf(self.topDownTab), QCoreApplication.translate("LYTEditor", u"Top-Down View", None))
        self.viewTabWidget.setTabText(self.viewTabWidget.indexOf(self.threeDTab), QCoreApplication.translate("LYTEditor", u"3D View", None))
        self.addRoomButton.setText(QCoreApplication.translate("LYTEditor", u"Add Room", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.roomsTab), QCoreApplication.translate("LYTEditor", u"Rooms", None))
        self.addTrackButton.setText(QCoreApplication.translate("LYTEditor", u"Add Track", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tracksTab), QCoreApplication.translate("LYTEditor", u"Tracks", None))
        self.addObstacleButton.setText(QCoreApplication.translate("LYTEditor", u"Add Obstacle", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.obstaclesTab), QCoreApplication.translate("LYTEditor", u"Obstacles", None))
        self.addDoorHookButton.setText(QCoreApplication.translate("LYTEditor", u"Add Door Hook", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.doorhooksTab), QCoreApplication.translate("LYTEditor", u"Doorhooks", None))
        self.texturesGroupBox.setTitle(QCoreApplication.translate("LYTEditor", u"Textures", None))
        self.importTextureButton.setText(QCoreApplication.translate("LYTEditor", u"Import Texture", None))
        self.roomTemplatesGroupBox.setTitle(QCoreApplication.translate("LYTEditor", u"Room Templates", None))
        self.importModelButton.setText(QCoreApplication.translate("LYTEditor", u"Import Model", None))
        self.generateWalkmeshButton.setText(QCoreApplication.translate("LYTEditor", u"Generate Walkmesh", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
