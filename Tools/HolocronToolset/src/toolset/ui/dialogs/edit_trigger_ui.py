
################################################################################
## Form generated from reading UI file 'edit_trigger.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, Qt
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
)


class Ui_Dialog:
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName("Dialog")
        Dialog.resize(330, 97)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label = QLabel(Dialog)
        self.label.setObjectName("label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.xPosSpin = QDoubleSpinBox(Dialog)
        self.xPosSpin.setObjectName("xPosSpin")
        self.xPosSpin.setMinimum(-1000000.000000000000000)
        self.xPosSpin.setMaximum(1000000.000000000000000)

        self.horizontalLayout.addWidget(self.xPosSpin)

        self.yPosSpin = QDoubleSpinBox(Dialog)
        self.yPosSpin.setObjectName("yPosSpin")
        self.yPosSpin.setMinimum(-1000000.000000000000000)
        self.yPosSpin.setMaximum(1000000.000000000000000)

        self.horizontalLayout.addWidget(self.yPosSpin)

        self.zPosSpin = QDoubleSpinBox(Dialog)
        self.zPosSpin.setObjectName("zPosSpin")
        self.zPosSpin.setMinimum(-1000000.000000000000000)
        self.zPosSpin.setMaximum(1000000.000000000000000)

        self.horizontalLayout.addWidget(self.zPosSpin)


        self.formLayout.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout)

        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName("label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.resrefEdit = QLineEdit(Dialog)
        self.resrefEdit.setObjectName("resrefEdit")
        self.resrefEdit.setMaxLength(16)

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.resrefEdit)


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
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", "Edit Trigger", None))
        self.label.setText(QCoreApplication.translate("Dialog", "Position:", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", "ResRef:", None))
    # retranslateUi

