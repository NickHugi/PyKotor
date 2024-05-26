# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'audio_player.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QMainWindow,
    QMenu, QMenuBar, QPushButton, QSizePolicy,
    QSlider, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(351, 94)
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName(u"actionOpen")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.currentTimeLabel = QLabel(self.centralwidget)
        self.currentTimeLabel.setObjectName(u"currentTimeLabel")
        self.currentTimeLabel.setMinimumSize(QSize(60, 0))
        self.currentTimeLabel.setAlignment(Qt.AlignCenter)

        self.horizontalLayout.addWidget(self.currentTimeLabel)

        self.timeSlider = QSlider(self.centralwidget)
        self.timeSlider.setObjectName(u"timeSlider")
        self.timeSlider.setOrientation(Qt.Horizontal)

        self.horizontalLayout.addWidget(self.timeSlider)

        self.totalTimeLabel = QLabel(self.centralwidget)
        self.totalTimeLabel.setObjectName(u"totalTimeLabel")
        self.totalTimeLabel.setMinimumSize(QSize(60, 0))
        self.totalTimeLabel.setAlignment(Qt.AlignCenter)

        self.horizontalLayout.addWidget(self.totalTimeLabel)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.playButton = QPushButton(self.centralwidget)
        self.playButton.setObjectName(u"playButton")

        self.horizontalLayout_2.addWidget(self.playButton)

        self.pauseButton = QPushButton(self.centralwidget)
        self.pauseButton.setObjectName(u"pauseButton")

        self.horizontalLayout_2.addWidget(self.pauseButton)

        self.stopButton = QPushButton(self.centralwidget)
        self.stopButton.setObjectName(u"stopButton")

        self.horizontalLayout_2.addWidget(self.stopButton)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 351, 21))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menuFile.addAction(self.actionOpen)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Audio Player", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", u"Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.currentTimeLabel.setText(QCoreApplication.translate("MainWindow", u"00:00:00", None))
        self.totalTimeLabel.setText(QCoreApplication.translate("MainWindow", u"00:00:00", None))
        self.playButton.setText(QCoreApplication.translate("MainWindow", u"Play", None))
        self.pauseButton.setText(QCoreApplication.translate("MainWindow", u"Pause", None))
        self.stopButton.setText(QCoreApplication.translate("MainWindow", u"Stop", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside6
