
################################################################################
## Form generated from reading UI file 'indoor_settings.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QSize, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from toolset.gui.widgets.edit.color import ColorEdit
from toolset.gui.widgets.edit.locstring import LocalizedStringLineEdit


class Ui_Dialog:
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName("Dialog")
        Dialog.resize(285, 157)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label = QLabel(Dialog)
        self.label.setObjectName("label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName("horizontalLayout_14")
        self.nameEdit = LocalizedStringLineEdit(Dialog)
        self.nameEdit.setObjectName("nameEdit")
        self.nameEdit.setMinimumSize(QSize(0, 23))

        self.horizontalLayout_14.addWidget(self.nameEdit)


        self.formLayout.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout_14)

        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName("label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        self.colorEdit = ColorEdit(Dialog)
        self.colorEdit.setObjectName("colorEdit")
        self.colorEdit.setMinimumSize(QSize(0, 23))

        self.horizontalLayout_13.addWidget(self.colorEdit)


        self.formLayout.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout_13)

        self.label_3 = QLabel(Dialog)
        self.label_3.setObjectName("label_3")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_3)

        self.warpCodeEdit = QLineEdit(Dialog)
        self.warpCodeEdit.setObjectName("warpCodeEdit")
        self.warpCodeEdit.setMaxLength(6)

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.warpCodeEdit)

        self.skyboxSelect = QComboBox(Dialog)
        self.skyboxSelect.setObjectName("skyboxSelect")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.skyboxSelect)

        self.label_4 = QLabel(Dialog)
        self.label_4.setObjectName("label_4")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_4)


        self.verticalLayout.addLayout(self.formLayout)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName("buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", "Module Settings", None))
        self.label.setText(QCoreApplication.translate("Dialog", "Name:", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", "Lighting:", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", "Warp Code:", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", "Skybox:", None))
    # retranslateUi

