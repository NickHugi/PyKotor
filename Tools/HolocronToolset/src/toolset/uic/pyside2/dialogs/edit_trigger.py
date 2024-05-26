# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'edit_trigger.ui'
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
        Dialog.resize(330, 97)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.xPosSpin = QDoubleSpinBox(Dialog)
        self.xPosSpin.setObjectName(u"xPosSpin")
        self.xPosSpin.setMinimum(-1000000.000000000000000)
        self.xPosSpin.setMaximum(1000000.000000000000000)

        self.horizontalLayout.addWidget(self.xPosSpin)

        self.yPosSpin = QDoubleSpinBox(Dialog)
        self.yPosSpin.setObjectName(u"yPosSpin")
        self.yPosSpin.setMinimum(-1000000.000000000000000)
        self.yPosSpin.setMaximum(1000000.000000000000000)

        self.horizontalLayout.addWidget(self.yPosSpin)

        self.zPosSpin = QDoubleSpinBox(Dialog)
        self.zPosSpin.setObjectName(u"zPosSpin")
        self.zPosSpin.setMinimum(-1000000.000000000000000)
        self.zPosSpin.setMaximum(1000000.000000000000000)

        self.horizontalLayout.addWidget(self.zPosSpin)


        self.formLayout.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout)

        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.resrefEdit = QLineEdit(Dialog)
        self.resrefEdit.setObjectName(u"resrefEdit")
        self.resrefEdit.setMaxLength(16)

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.resrefEdit)


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
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Edit Trigger", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Position:", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"ResRef:", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
