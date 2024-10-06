
################################################################################
## Form generated from reading UI file 'lyt_editor.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, Qt
from PySide6.QtWidgets import (
    QGraphicsView,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QSlider,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class Ui_LYTEditor:
    def setupUi(self, LYTEditor):
        if not LYTEditor.objectName():
            LYTEditor.setObjectName("LYTEditor")
        LYTEditor.resize(800, 600)
        self.horizontalLayout = QHBoxLayout(LYTEditor)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.splitter = QSplitter(LYTEditor)
        self.splitter.setObjectName("splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.leftPanel = QWidget(self.splitter)
        self.leftPanel.setObjectName("leftPanel")
        self.verticalLayout = QVBoxLayout(self.leftPanel)
        self.verticalLayout.setObjectName("verticalLayout")
        self.graphicsView = QGraphicsView(self.leftPanel)
        self.graphicsView.setObjectName("graphicsView")

        self.verticalLayout.addWidget(self.graphicsView)

        self.zoomSlider = QSlider(self.leftPanel)
        self.zoomSlider.setObjectName("zoomSlider")
        self.zoomSlider.setOrientation(Qt.Horizontal)

        self.verticalLayout.addWidget(self.zoomSlider)

        self.splitter.addWidget(self.leftPanel)
        self.rightPanel = QWidget(self.splitter)
        self.rightPanel.setObjectName("rightPanel")
        self.verticalLayout_2 = QVBoxLayout(self.rightPanel)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.tabWidget = QTabWidget(self.rightPanel)
        self.tabWidget.setObjectName("tabWidget")
        self.roomsTab = QWidget()
        self.roomsTab.setObjectName("roomsTab")
        self.verticalLayout_3 = QVBoxLayout(self.roomsTab)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.roomsList = QListWidget(self.roomsTab)
        self.roomsList.setObjectName("roomsList")

        self.verticalLayout_3.addWidget(self.roomsList)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.addRoomButton = QPushButton(self.roomsTab)
        self.addRoomButton.setObjectName("addRoomButton")

        self.horizontalLayout_2.addWidget(self.addRoomButton)

        self.editRoomButton = QPushButton(self.roomsTab)
        self.editRoomButton.setObjectName("editRoomButton")

        self.horizontalLayout_2.addWidget(self.editRoomButton)

        self.deleteRoomButton = QPushButton(self.roomsTab)
        self.deleteRoomButton.setObjectName("deleteRoomButton")

        self.horizontalLayout_2.addWidget(self.deleteRoomButton)


        self.verticalLayout_3.addLayout(self.horizontalLayout_2)

        self.tabWidget.addTab(self.roomsTab, "")
        self.tracksTab = QWidget()
        self.tracksTab.setObjectName("tracksTab")
        self.verticalLayout_4 = QVBoxLayout(self.tracksTab)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.tracksList = QListWidget(self.tracksTab)
        self.tracksList.setObjectName("tracksList")

        self.verticalLayout_4.addWidget(self.tracksList)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.addTrackButton = QPushButton(self.tracksTab)
        self.addTrackButton.setObjectName("addTrackButton")

        self.horizontalLayout_3.addWidget(self.addTrackButton)

        self.editTrackButton = QPushButton(self.tracksTab)
        self.editTrackButton.setObjectName("editTrackButton")

        self.horizontalLayout_3.addWidget(self.editTrackButton)

        self.deleteTrackButton = QPushButton(self.tracksTab)
        self.deleteTrackButton.setObjectName("deleteTrackButton")

        self.horizontalLayout_3.addWidget(self.deleteTrackButton)


        self.verticalLayout_4.addLayout(self.horizontalLayout_3)

        self.tabWidget.addTab(self.tracksTab, "")
        self.obstaclesTab = QWidget()
        self.obstaclesTab.setObjectName("obstaclesTab")
        self.verticalLayout_5 = QVBoxLayout(self.obstaclesTab)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.obstaclesList = QListWidget(self.obstaclesTab)
        self.obstaclesList.setObjectName("obstaclesList")

        self.verticalLayout_5.addWidget(self.obstaclesList)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.addObstacleButton = QPushButton(self.obstaclesTab)
        self.addObstacleButton.setObjectName("addObstacleButton")

        self.horizontalLayout_4.addWidget(self.addObstacleButton)

        self.editObstacleButton = QPushButton(self.obstaclesTab)
        self.editObstacleButton.setObjectName("editObstacleButton")

        self.horizontalLayout_4.addWidget(self.editObstacleButton)

        self.deleteObstacleButton = QPushButton(self.obstaclesTab)
        self.deleteObstacleButton.setObjectName("deleteObstacleButton")

        self.horizontalLayout_4.addWidget(self.deleteObstacleButton)


        self.verticalLayout_5.addLayout(self.horizontalLayout_4)

        self.tabWidget.addTab(self.obstaclesTab, "")
        self.doorhooksTab = QWidget()
        self.doorhooksTab.setObjectName("doorhooksTab")
        self.verticalLayout_6 = QVBoxLayout(self.doorhooksTab)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.doorhooksList = QListWidget(self.doorhooksTab)
        self.doorhooksList.setObjectName("doorhooksList")

        self.verticalLayout_6.addWidget(self.doorhooksList)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.addDoorhookButton = QPushButton(self.doorhooksTab)
        self.addDoorhookButton.setObjectName("addDoorhookButton")

        self.horizontalLayout_5.addWidget(self.addDoorhookButton)

        self.editDoorhookButton = QPushButton(self.doorhooksTab)
        self.editDoorhookButton.setObjectName("editDoorhookButton")

        self.horizontalLayout_5.addWidget(self.editDoorhookButton)

        self.deleteDoorhookButton = QPushButton(self.doorhooksTab)
        self.deleteDoorhookButton.setObjectName("deleteDoorhookButton")

        self.horizontalLayout_5.addWidget(self.deleteDoorhookButton)


        self.verticalLayout_6.addLayout(self.horizontalLayout_5)

        self.tabWidget.addTab(self.doorhooksTab, "")

        self.verticalLayout_2.addWidget(self.tabWidget)

        self.generateWalkmeshButton = QPushButton(self.rightPanel)
        self.generateWalkmeshButton.setObjectName("generateWalkmeshButton")

        self.verticalLayout_2.addWidget(self.generateWalkmeshButton)

        self.splitter.addWidget(self.rightPanel)

        self.horizontalLayout.addWidget(self.splitter)


        self.retranslateUi(LYTEditor)

        QMetaObject.connectSlotsByName(LYTEditor)
    # setupUi

    def retranslateUi(self, LYTEditor):
        LYTEditor.setWindowTitle(QCoreApplication.translate("LYTEditor", "LYT Editor", None))
        self.addRoomButton.setText(QCoreApplication.translate("LYTEditor", "Add Room", None))
        self.editRoomButton.setText(QCoreApplication.translate("LYTEditor", "Edit Room", None))
        self.deleteRoomButton.setText(QCoreApplication.translate("LYTEditor", "Delete Room", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.roomsTab), QCoreApplication.translate("LYTEditor", "Rooms", None))
        self.addTrackButton.setText(QCoreApplication.translate("LYTEditor", "Add Track", None))
        self.editTrackButton.setText(QCoreApplication.translate("LYTEditor", "Edit Track", None))
        self.deleteTrackButton.setText(QCoreApplication.translate("LYTEditor", "Delete Track", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tracksTab), QCoreApplication.translate("LYTEditor", "Tracks", None))
        self.addObstacleButton.setText(QCoreApplication.translate("LYTEditor", "Add Obstacle", None))
        self.editObstacleButton.setText(QCoreApplication.translate("LYTEditor", "Edit Obstacle", None))
        self.deleteObstacleButton.setText(QCoreApplication.translate("LYTEditor", "Delete Obstacle", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.obstaclesTab), QCoreApplication.translate("LYTEditor", "Obstacles", None))
        self.addDoorhookButton.setText(QCoreApplication.translate("LYTEditor", "Add Doorhook", None))
        self.editDoorhookButton.setText(QCoreApplication.translate("LYTEditor", "Edit Doorhook", None))
        self.deleteDoorhookButton.setText(QCoreApplication.translate("LYTEditor", "Delete Doorhook", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.doorhooksTab), QCoreApplication.translate("LYTEditor", "Doorhooks", None))
        self.generateWalkmeshButton.setText(QCoreApplication.translate("LYTEditor", "Generate Walkmesh", None))
    # retranslateUi

