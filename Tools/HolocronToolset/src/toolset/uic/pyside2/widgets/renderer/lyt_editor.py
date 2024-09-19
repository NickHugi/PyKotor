# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'lyt_editor.ui'
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
        LYTEditor.resize(800, 600)
        self.horizontalLayout = QHBoxLayout(LYTEditor)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.splitter = QSplitter(LYTEditor)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.leftPanel = QWidget(self.splitter)
        self.leftPanel.setObjectName(u"leftPanel")
        self.verticalLayout = QVBoxLayout(self.leftPanel)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.graphicsView = QGraphicsView(self.leftPanel)
        self.graphicsView.setObjectName(u"graphicsView")

        self.verticalLayout.addWidget(self.graphicsView)

        self.zoomSlider = QSlider(self.leftPanel)
        self.zoomSlider.setObjectName(u"zoomSlider")
        self.zoomSlider.setOrientation(Qt.Horizontal)

        self.verticalLayout.addWidget(self.zoomSlider)

        self.splitter.addWidget(self.leftPanel)
        self.rightPanel = QWidget(self.splitter)
        self.rightPanel.setObjectName(u"rightPanel")
        self.verticalLayout_2 = QVBoxLayout(self.rightPanel)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.tabWidget = QTabWidget(self.rightPanel)
        self.tabWidget.setObjectName(u"tabWidget")
        self.roomsTab = QWidget()
        self.roomsTab.setObjectName(u"roomsTab")
        self.verticalLayout_3 = QVBoxLayout(self.roomsTab)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.roomsList = QListWidget(self.roomsTab)
        self.roomsList.setObjectName(u"roomsList")

        self.verticalLayout_3.addWidget(self.roomsList)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.addRoomButton = QPushButton(self.roomsTab)
        self.addRoomButton.setObjectName(u"addRoomButton")

        self.horizontalLayout_2.addWidget(self.addRoomButton)

        self.editRoomButton = QPushButton(self.roomsTab)
        self.editRoomButton.setObjectName(u"editRoomButton")

        self.horizontalLayout_2.addWidget(self.editRoomButton)

        self.deleteRoomButton = QPushButton(self.roomsTab)
        self.deleteRoomButton.setObjectName(u"deleteRoomButton")

        self.horizontalLayout_2.addWidget(self.deleteRoomButton)


        self.verticalLayout_3.addLayout(self.horizontalLayout_2)

        self.tabWidget.addTab(self.roomsTab, "")
        self.tracksTab = QWidget()
        self.tracksTab.setObjectName(u"tracksTab")
        self.verticalLayout_4 = QVBoxLayout(self.tracksTab)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.tracksList = QListWidget(self.tracksTab)
        self.tracksList.setObjectName(u"tracksList")

        self.verticalLayout_4.addWidget(self.tracksList)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.addTrackButton = QPushButton(self.tracksTab)
        self.addTrackButton.setObjectName(u"addTrackButton")

        self.horizontalLayout_3.addWidget(self.addTrackButton)

        self.editTrackButton = QPushButton(self.tracksTab)
        self.editTrackButton.setObjectName(u"editTrackButton")

        self.horizontalLayout_3.addWidget(self.editTrackButton)

        self.deleteTrackButton = QPushButton(self.tracksTab)
        self.deleteTrackButton.setObjectName(u"deleteTrackButton")

        self.horizontalLayout_3.addWidget(self.deleteTrackButton)


        self.verticalLayout_4.addLayout(self.horizontalLayout_3)

        self.tabWidget.addTab(self.tracksTab, "")
        self.obstaclesTab = QWidget()
        self.obstaclesTab.setObjectName(u"obstaclesTab")
        self.verticalLayout_5 = QVBoxLayout(self.obstaclesTab)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.obstaclesList = QListWidget(self.obstaclesTab)
        self.obstaclesList.setObjectName(u"obstaclesList")

        self.verticalLayout_5.addWidget(self.obstaclesList)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.addObstacleButton = QPushButton(self.obstaclesTab)
        self.addObstacleButton.setObjectName(u"addObstacleButton")

        self.horizontalLayout_4.addWidget(self.addObstacleButton)

        self.editObstacleButton = QPushButton(self.obstaclesTab)
        self.editObstacleButton.setObjectName(u"editObstacleButton")

        self.horizontalLayout_4.addWidget(self.editObstacleButton)

        self.deleteObstacleButton = QPushButton(self.obstaclesTab)
        self.deleteObstacleButton.setObjectName(u"deleteObstacleButton")

        self.horizontalLayout_4.addWidget(self.deleteObstacleButton)


        self.verticalLayout_5.addLayout(self.horizontalLayout_4)

        self.tabWidget.addTab(self.obstaclesTab, "")
        self.doorhooksTab = QWidget()
        self.doorhooksTab.setObjectName(u"doorhooksTab")
        self.verticalLayout_6 = QVBoxLayout(self.doorhooksTab)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.doorhooksList = QListWidget(self.doorhooksTab)
        self.doorhooksList.setObjectName(u"doorhooksList")

        self.verticalLayout_6.addWidget(self.doorhooksList)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.addDoorhookButton = QPushButton(self.doorhooksTab)
        self.addDoorhookButton.setObjectName(u"addDoorhookButton")

        self.horizontalLayout_5.addWidget(self.addDoorhookButton)

        self.editDoorhookButton = QPushButton(self.doorhooksTab)
        self.editDoorhookButton.setObjectName(u"editDoorhookButton")

        self.horizontalLayout_5.addWidget(self.editDoorhookButton)

        self.deleteDoorhookButton = QPushButton(self.doorhooksTab)
        self.deleteDoorhookButton.setObjectName(u"deleteDoorhookButton")

        self.horizontalLayout_5.addWidget(self.deleteDoorhookButton)


        self.verticalLayout_6.addLayout(self.horizontalLayout_5)

        self.tabWidget.addTab(self.doorhooksTab, "")

        self.verticalLayout_2.addWidget(self.tabWidget)

        self.generateWalkmeshButton = QPushButton(self.rightPanel)
        self.generateWalkmeshButton.setObjectName(u"generateWalkmeshButton")

        self.verticalLayout_2.addWidget(self.generateWalkmeshButton)

        self.splitter.addWidget(self.rightPanel)

        self.horizontalLayout.addWidget(self.splitter)


        self.retranslateUi(LYTEditor)

        QMetaObject.connectSlotsByName(LYTEditor)
    # setupUi

    def retranslateUi(self, LYTEditor):
        LYTEditor.setWindowTitle(QCoreApplication.translate("LYTEditor", u"LYT Editor", None))
        self.addRoomButton.setText(QCoreApplication.translate("LYTEditor", u"Add Room", None))
        self.editRoomButton.setText(QCoreApplication.translate("LYTEditor", u"Edit Room", None))
        self.deleteRoomButton.setText(QCoreApplication.translate("LYTEditor", u"Delete Room", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.roomsTab), QCoreApplication.translate("LYTEditor", u"Rooms", None))
        self.addTrackButton.setText(QCoreApplication.translate("LYTEditor", u"Add Track", None))
        self.editTrackButton.setText(QCoreApplication.translate("LYTEditor", u"Edit Track", None))
        self.deleteTrackButton.setText(QCoreApplication.translate("LYTEditor", u"Delete Track", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tracksTab), QCoreApplication.translate("LYTEditor", u"Tracks", None))
        self.addObstacleButton.setText(QCoreApplication.translate("LYTEditor", u"Add Obstacle", None))
        self.editObstacleButton.setText(QCoreApplication.translate("LYTEditor", u"Edit Obstacle", None))
        self.deleteObstacleButton.setText(QCoreApplication.translate("LYTEditor", u"Delete Obstacle", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.obstaclesTab), QCoreApplication.translate("LYTEditor", u"Obstacles", None))
        self.addDoorhookButton.setText(QCoreApplication.translate("LYTEditor", u"Add Doorhook", None))
        self.editDoorhookButton.setText(QCoreApplication.translate("LYTEditor", u"Edit Doorhook", None))
        self.deleteDoorhookButton.setText(QCoreApplication.translate("LYTEditor", u"Delete Doorhook", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.doorhooksTab), QCoreApplication.translate("LYTEditor", u"Doorhooks", None))
        self.generateWalkmeshButton.setText(QCoreApplication.translate("LYTEditor", u"Generate Walkmesh", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
