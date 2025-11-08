# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'installations.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(412, 243)
        self.horizontalLayout = QHBoxLayout(Form)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.pathList = QListView(Form)
        self.pathList.setObjectName(u"pathList")
        self.pathList.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.verticalLayout_2.addWidget(self.pathList)

        self.addPathButton = QPushButton(Form)
        self.addPathButton.setObjectName(u"addPathButton")

        self.verticalLayout_2.addWidget(self.addPathButton)

        self.removePathButton = QPushButton(Form)
        self.removePathButton.setObjectName(u"removePathButton")

        self.verticalLayout_2.addWidget(self.removePathButton)


        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.line = QFrame(Form)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout.addWidget(self.line)

        self.pathFrame = QFrame(Form)
        self.pathFrame.setObjectName(u"pathFrame")
        self.pathFrame.setEnabled(False)
        self.pathFrame.setFrameShape(QFrame.StyledPanel)
        self.pathFrame.setFrameShadow(QFrame.Raised)
        self.formLayout_2 = QFormLayout(self.pathFrame)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label_11 = QLabel(self.pathFrame)
        self.label_11.setObjectName(u"label_11")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_11)

        self.pathNameEdit = QLineEdit(self.pathFrame)
        self.pathNameEdit.setObjectName(u"pathNameEdit")

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.pathNameEdit)

        self.label_12 = QLabel(self.pathFrame)
        self.label_12.setObjectName(u"label_12")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_12)

        self.pathDirEdit = QLineEdit(self.pathFrame)
        self.pathDirEdit.setObjectName(u"pathDirEdit")

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.pathDirEdit)

        self.label_13 = QLabel(self.pathFrame)
        self.label_13.setObjectName(u"label_13")

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.label_13)

        self.pathTslCheckbox = QCheckBox(self.pathFrame)
        self.pathTslCheckbox.setObjectName(u"pathTslCheckbox")

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.pathTslCheckbox)


        self.horizontalLayout.addWidget(self.pathFrame)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(2, 2)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.addPathButton.setText(QCoreApplication.translate("Form", u"Add", None))
        self.removePathButton.setText(QCoreApplication.translate("Form", u"Remove", None))
        self.label_11.setText(QCoreApplication.translate("Form", u"Name:", None))
        self.label_12.setText(QCoreApplication.translate("Form", u"Path:", None))
        self.label_13.setText(QCoreApplication.translate("Form", u"TSL:", None))
        self.pathTslCheckbox.setText("")
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
