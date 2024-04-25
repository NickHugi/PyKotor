# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'color_edit.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from toolset.gui.widgets.long_spinbox import LongSpinBox


class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(235, 23)
        self.horizontalLayout = QHBoxLayout(Form)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.colorLabel = QLabel(Form)
        self.colorLabel.setObjectName(u"colorLabel")
        self.colorLabel.setMinimumSize(QSize(16, 16))
        self.colorLabel.setMaximumSize(QSize(16, 16))
        self.colorLabel.setStyleSheet(u"background: black;")

        self.horizontalLayout.addWidget(self.colorLabel)

        self.colorSpin = LongSpinBox(Form)
        self.colorSpin.setObjectName(u"colorSpin")

        self.horizontalLayout.addWidget(self.colorSpin)

        self.editButton = QPushButton(Form)
        self.editButton.setObjectName(u"editButton")
        self.editButton.setMaximumSize(QSize(26, 23))

        self.horizontalLayout.addWidget(self.editButton)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.colorLabel.setText("")
        self.editButton.setText(QCoreApplication.translate("Form", u"...", None))
    # retranslateUi

