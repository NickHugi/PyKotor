
################################################################################
## Form generated from reading UI file 'installations.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject
from PySide6.QtWidgets import QAbstractItemView, QCheckBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from utility.ui_libraries.qt.widgets.itemviews.listview import RobustListView


class Ui_Form:
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName("Form")
        Form.resize(412, 243)
        self.horizontalLayout = QHBoxLayout(Form)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.pathList = RobustListView(Form)
        self.pathList.setObjectName("pathList")
        self.pathList.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.verticalLayout_2.addWidget(self.pathList)

        self.addPathButton = QPushButton(Form)
        self.addPathButton.setObjectName("addPathButton")

        self.verticalLayout_2.addWidget(self.addPathButton)

        self.removePathButton = QPushButton(Form)
        self.removePathButton.setObjectName("removePathButton")

        self.verticalLayout_2.addWidget(self.removePathButton)


        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.line = QFrame(Form)
        self.line.setObjectName("line")
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout.addWidget(self.line)

        self.pathFrame = QFrame(Form)
        self.pathFrame.setObjectName("pathFrame")
        self.pathFrame.setEnabled(False)
        self.pathFrame.setFrameShape(QFrame.StyledPanel)
        self.pathFrame.setFrameShadow(QFrame.Raised)
        self.formLayout_2 = QFormLayout(self.pathFrame)
        self.formLayout_2.setObjectName("formLayout_2")
        self.label_11 = QLabel(self.pathFrame)
        self.label_11.setObjectName("label_11")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_11)

        self.pathNameEdit = QLineEdit(self.pathFrame)
        self.pathNameEdit.setObjectName("pathNameEdit")

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.pathNameEdit)

        self.label_12 = QLabel(self.pathFrame)
        self.label_12.setObjectName("label_12")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_12)

        self.pathDirEdit = QLineEdit(self.pathFrame)
        self.pathDirEdit.setObjectName("pathDirEdit")

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.pathDirEdit)

        self.label_13 = QLabel(self.pathFrame)
        self.label_13.setObjectName("label_13")

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.label_13)

        self.pathTslCheckbox = QCheckBox(self.pathFrame)
        self.pathTslCheckbox.setObjectName("pathTslCheckbox")

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.pathTslCheckbox)


        self.horizontalLayout.addWidget(self.pathFrame)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(2, 2)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", "Form", None))
        self.addPathButton.setText(QCoreApplication.translate("Form", "Add", None))
        self.removePathButton.setText(QCoreApplication.translate("Form", "Remove", None))
        self.label_11.setText(QCoreApplication.translate("Form", "Name:", None))
        self.label_12.setText(QCoreApplication.translate("Form", "Path:", None))
        self.label_13.setText(QCoreApplication.translate("Form", "TSL:", None))
        self.pathTslCheckbox.setText("")
    # retranslateUi

