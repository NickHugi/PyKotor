
################################################################################
## Form generated from reading UI file 'audio_player.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMenu, QMenuBar, QPushButton, QSlider, QVBoxLayout, QWidget


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(351, 94)
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.currentTimeLabel = QLabel(self.centralwidget)
        self.currentTimeLabel.setObjectName("currentTimeLabel")
        self.currentTimeLabel.setMinimumSize(QSize(60, 0))
        self.currentTimeLabel.setAlignment(Qt.AlignCenter)

        self.horizontalLayout.addWidget(self.currentTimeLabel)

        self.timeSlider = QSlider(self.centralwidget)
        self.timeSlider.setObjectName("timeSlider")
        self.timeSlider.setOrientation(Qt.Horizontal)

        self.horizontalLayout.addWidget(self.timeSlider)

        self.totalTimeLabel = QLabel(self.centralwidget)
        self.totalTimeLabel.setObjectName("totalTimeLabel")
        self.totalTimeLabel.setMinimumSize(QSize(60, 0))
        self.totalTimeLabel.setAlignment(Qt.AlignCenter)

        self.horizontalLayout.addWidget(self.totalTimeLabel)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.playButton = QPushButton(self.centralwidget)
        self.playButton.setObjectName("playButton")

        self.horizontalLayout_2.addWidget(self.playButton)

        self.pauseButton = QPushButton(self.centralwidget)
        self.pauseButton.setObjectName("pauseButton")

        self.horizontalLayout_2.addWidget(self.pauseButton)

        self.stopButton = QPushButton(self.centralwidget)
        self.stopButton.setObjectName("stopButton")

        self.horizontalLayout_2.addWidget(self.stopButton)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 351, 21))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menuFile.addAction(self.actionOpen)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", "Audio Player", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", "Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", "Save", None))
        self.currentTimeLabel.setText(QCoreApplication.translate("MainWindow", "00:00:00", None))
        self.totalTimeLabel.setText(QCoreApplication.translate("MainWindow", "00:00:00", None))
        self.playButton.setText(QCoreApplication.translate("MainWindow", "Play", None))
        self.pauseButton.setText(QCoreApplication.translate("MainWindow", "Pause", None))
        self.stopButton.setText(QCoreApplication.translate("MainWindow", "Stop", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", "File", None))
    # retranslateUi

