
################################################################################
## Form generated from reading UI file 'locstring.ui'
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
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QVBoxLayout,
)


class Ui_Dialog:
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName("Dialog")
        Dialog.resize(355, 214)
        Dialog.setMinimumSize(QSize(300, 150))
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.frame = QFrame(Dialog)
        self.frame.setObjectName("frame")
        self.frame.setFrameShape(QFrame.NoFrame)
        self.frame.setFrameShadow(QFrame.Plain)
        self.horizontalLayout_2 = QHBoxLayout(self.frame)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.label_2 = QLabel(self.frame)
        self.label_2.setObjectName("label_2")

        self.horizontalLayout_2.addWidget(self.label_2)

        self.stringrefSpin = QSpinBox(self.frame)
        self.stringrefSpin.setObjectName("stringrefSpin")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.stringrefSpin.sizePolicy().hasHeightForWidth())
        self.stringrefSpin.setSizePolicy(sizePolicy)
        self.stringrefSpin.setMinimum(-1)
        self.stringrefSpin.setMaximum(999999999)

        self.horizontalLayout_2.addWidget(self.stringrefSpin)

        self.stringrefNewButton = QPushButton(self.frame)
        self.stringrefNewButton.setObjectName("stringrefNewButton")
        self.stringrefNewButton.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_2.addWidget(self.stringrefNewButton)

        self.stringrefNoneButton = QPushButton(self.frame)
        self.stringrefNoneButton.setObjectName("stringrefNoneButton")
        self.stringrefNoneButton.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_2.addWidget(self.stringrefNoneButton)

        self.horizontalLayout_2.setStretch(1, 1)

        self.verticalLayout.addWidget(self.frame)

        self.substringFrame = QFrame(Dialog)
        self.substringFrame.setObjectName("substringFrame")
        self.substringFrame.setFrameShape(QFrame.NoFrame)
        self.substringFrame.setFrameShadow(QFrame.Plain)
        self.horizontalLayout = QHBoxLayout(self.substringFrame)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.languageSelect = QComboBox(self.substringFrame)
        self.languageSelect.addItem("")
        self.languageSelect.addItem("")
        self.languageSelect.addItem("")
        self.languageSelect.addItem("")
        self.languageSelect.addItem("")
        self.languageSelect.addItem("")
        self.languageSelect.setObjectName("languageSelect")
        self.languageSelect.setMinimumSize(QSize(160, 0))

        self.horizontalLayout.addWidget(self.languageSelect)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.maleRadio = QRadioButton(self.substringFrame)
        self.maleRadio.setObjectName("maleRadio")
        self.maleRadio.setChecked(True)

        self.horizontalLayout.addWidget(self.maleRadio)

        self.femaleRadio = QRadioButton(self.substringFrame)
        self.femaleRadio.setObjectName("femaleRadio")

        self.horizontalLayout.addWidget(self.femaleRadio)

        self.horizontalLayout.setStretch(0, 1)

        self.verticalLayout.addWidget(self.substringFrame)

        self.stringEdit = QPlainTextEdit(Dialog)
        self.stringEdit.setObjectName("stringEdit")

        self.verticalLayout.addWidget(self.stringEdit)

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
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", "Edit Localized String", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", "StringRef:", None))
        self.stringrefNewButton.setText(QCoreApplication.translate("Dialog", "New", None))
        self.stringrefNoneButton.setText(QCoreApplication.translate("Dialog", "None", None))
        self.languageSelect.setItemText(0, QCoreApplication.translate("Dialog", "English", None))
        self.languageSelect.setItemText(1, QCoreApplication.translate("Dialog", "French", None))
        self.languageSelect.setItemText(2, QCoreApplication.translate("Dialog", "German", None))
        self.languageSelect.setItemText(3, QCoreApplication.translate("Dialog", "Italian", None))
        self.languageSelect.setItemText(4, QCoreApplication.translate("Dialog", "Spanish", None))
        self.languageSelect.setItemText(5, QCoreApplication.translate("Dialog", "Polish", None))

        self.maleRadio.setText(QCoreApplication.translate("Dialog", "Male", None))
        self.femaleRadio.setText(QCoreApplication.translate("Dialog", "Female", None))
    # retranslateUi

