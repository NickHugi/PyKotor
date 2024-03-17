# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'about.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDialog, QLabel, QPushButton,
    QSizePolicy, QWidget)
import resources_rc

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(430, 162)
        self.image = QLabel(Dialog)
        self.image.setObjectName(u"image")
        self.image.setGeometry(QRect(20, 20, 128, 128))
        self.image.setPixmap(QPixmap(u":/images/icons/sith.png"))
        self.image.setScaledContents(True)
        self.closeButton = QPushButton(Dialog)
        self.closeButton.setObjectName(u"closeButton")
        self.closeButton.setGeometry(QRect(340, 130, 75, 23))
        self.aboutLabel = QLabel(Dialog)
        self.aboutLabel.setObjectName(u"aboutLabel")
        self.aboutLabel.setGeometry(QRect(190, 10, 221, 111))
        self.aboutLabel.setOpenExternalLinks(True)

        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"About", None))
        self.image.setText("")
        self.closeButton.setText(QCoreApplication.translate("Dialog", u"Close", None))
        self.aboutLabel.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p><span style=\" font-size:10pt; font-weight:600;\">Holocron Toolset</span><br/>Version X.X.X<br/>Copyright (c) 2022 Nicholas Hugi</p><p><a href=\"https://sketchfab.com/3d-models/sith-holocron-star-wars-cb3d49a6261a4913817e8e00d6ab6e43\"><span style=\" text-decoration: underline; color:#0000ff;\">Holocron Image Source<br/></span></a><a href=\"https://deadlystream.com/profile/49753-cortisol/\"><span style=\" text-decoration: underline; color:#0000ff;\">Deadlystream Page<br/></span></a><a href=\"https://github.com/NickHugi/PyKotor\"><span style=\" text-decoration: underline; color:#0000ff;\">Github</span></a></p></body></html>", None))
    # retranslateUi

