
################################################################################
## Form generated from reading UI file 'color_edit.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QSize
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy

from toolset.gui.widgets.long_spinbox import LongSpinBox


class Ui_Form:
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName("Form")
        Form.resize(235, 23)
        self.horizontalLayout = QHBoxLayout(Form)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.colorLabel = QLabel(Form)
        self.colorLabel.setObjectName("colorLabel")
        self.colorLabel.setMinimumSize(QSize(16, 16))
        self.colorLabel.setMaximumSize(QSize(16, 16))
        self.colorLabel.setStyleSheet("background: black;")

        self.horizontalLayout.addWidget(self.colorLabel)

        self.colorSpin = LongSpinBox(Form)
        self.colorSpin.setObjectName("colorSpin")

        self.horizontalLayout.addWidget(self.colorSpin)

        self.editButton = QPushButton(Form)
        self.editButton.setObjectName("editButton")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.editButton.sizePolicy().hasHeightForWidth())
        self.editButton.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.editButton)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", "Form", None))
        self.colorLabel.setText("")
        self.editButton.setText(QCoreApplication.translate("Form", "Open ColorPicker", None))
    # retranslateUi

