# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'about.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from toolset.rcc import resources_rc_pyside2
class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(430, 207)
        self.image = QLabel(Dialog)
        self.image.setObjectName(u"image")
        self.image.setGeometry(QRect(20, 20, 128, 128))
        self.image.setPixmap(QPixmap(u":/images/icons/sith.png"))
        self.image.setScaledContents(True)
        self.verticalLayoutWidget = QWidget(Dialog)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(160, 20, 262, 169))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.aboutLabel = QLabel(self.verticalLayoutWidget)
        self.aboutLabel.setObjectName(u"aboutLabel")
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.aboutLabel.sizePolicy().hasHeightForWidth())
        self.aboutLabel.setSizePolicy(sizePolicy)
        self.aboutLabel.setOpenExternalLinks(True)

        self.horizontalLayout.addWidget(self.aboutLabel)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.closeButton = QPushButton(self.verticalLayoutWidget)
        self.closeButton.setObjectName(u"closeButton")

        self.horizontalLayout_2.addWidget(self.closeButton)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)


        self.verticalLayout.addLayout(self.horizontalLayout_2)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"About", None))
        self.image.setText("")
        self.aboutLabel.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p><span style=\" font-size:10pt; font-weight:600;\">Holocron Toolset</span><br/>Version X.X.X<br/>Copyright (c) 2022 Nicholas Hugi</p><p><a href=\"https://sketchfab.com/3d-models/sith-holocron-star-wars-cb3d49a6261a4913817e8e00d6ab6e43\"><span style=\" text-decoration: underline; color:#0000ff;\">Holocron Image Source<br/></span></a><a href=\"https://deadlystream.com/files/file/1982-holocron-toolset/\"><span style=\" text-decoration: underline; color:#0000ff;\">Deadlystream Page<br/></span></a><a href=\"https://github.com/NickHugi/PyKotor\"><span style=\" text-decoration: underline; color:#0000ff;\">Github</span></a></p></body></html>", None))
        self.closeButton.setText(QCoreApplication.translate("Dialog", u"Close", None))
    # retranslateUi

