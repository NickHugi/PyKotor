# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'save_to_module.ui'
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
        Dialog.resize(174, 95)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setLabelAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.resrefEdit = QLineEdit(Dialog)
        self.resrefEdit.setObjectName(u"resrefEdit")
        self.resrefEdit.setMaxLength(16)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.resrefEdit)

        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.typeCombo = QComboBox(Dialog)
        self.typeCombo.setObjectName(u"typeCombo")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.typeCombo)


        self.verticalLayout.addLayout(self.formLayout)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Save To Module", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"ResRef:", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Type:", None))
    # retranslateUi

