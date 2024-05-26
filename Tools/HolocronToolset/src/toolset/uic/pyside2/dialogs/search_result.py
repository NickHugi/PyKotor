# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'search_result.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(303, 401)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.resultList = QListWidget(Dialog)
        self.resultList.setObjectName(u"resultList")

        self.verticalLayout.addWidget(self.resultList)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.openButton = QPushButton(Dialog)
        self.openButton.setObjectName(u"openButton")

        self.horizontalLayout.addWidget(self.openButton)

        self.okButton = QPushButton(Dialog)
        self.okButton.setObjectName(u"okButton")

        self.horizontalLayout.addWidget(self.okButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Search Results", None))
        self.openButton.setText(QCoreApplication.translate("Dialog", u"Open", None))
        self.okButton.setText(QCoreApplication.translate("Dialog", u"OK", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
