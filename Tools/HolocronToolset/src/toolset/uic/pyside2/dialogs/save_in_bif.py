# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'save_in_bif.ui'
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
        Dialog.resize(271, 77)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.cancelButton = QPushButton(Dialog)
        self.cancelButton.setObjectName(u"cancelButton")

        self.horizontalLayout.addWidget(self.cancelButton)

        self.overrideSaveButton = QPushButton(Dialog)
        self.overrideSaveButton.setObjectName(u"overrideSaveButton")

        self.horizontalLayout.addWidget(self.overrideSaveButton)

        self.modSaveButton = QPushButton(Dialog)
        self.modSaveButton.setObjectName(u"modSaveButton")

        self.horizontalLayout.addWidget(self.modSaveButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Cannot save to RIM", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Saving to BIF files is unsupported. You can choose\n"
"to save it to the Override or .MOD file instead.", None))
        self.cancelButton.setText(QCoreApplication.translate("Dialog", u"Cancel", None))
        self.overrideSaveButton.setText(QCoreApplication.translate("Dialog", u"Save to Override", None))
        self.modSaveButton.setText(QCoreApplication.translate("Dialog", u"Save to .MOD", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
