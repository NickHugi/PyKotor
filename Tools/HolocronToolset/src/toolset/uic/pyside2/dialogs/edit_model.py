# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'edit_model.ui'
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
        Dialog.resize(401, 70)
        self.horizontalLayout = QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.participantEdit = QLineEdit(Dialog)
        self.participantEdit.setObjectName(u"participantEdit")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.participantEdit)

        self.stuntEdit = QLineEdit(Dialog)
        self.stuntEdit.setObjectName(u"stuntEdit")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.stuntEdit)


        self.horizontalLayout.addLayout(self.formLayout)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Vertical)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.horizontalLayout.addWidget(self.buttonBox)


        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Edit Cutscene Model", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Stunt Model:", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Participant:", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
