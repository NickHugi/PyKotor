# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'waypoint.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from toolset.gui.widgets.edit.locstring import LocalizedStringLineEdit


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(354, 266)
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

        self.resrefEdit = QLineEdit(Dialog)
        self.resrefEdit.setObjectName(u"resrefEdit")
        self.resrefEdit.setMaximumSize(QSize(187, 16777215))
        self.resrefEdit.setMaxLength(16)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.resrefEdit)

        self.label_8 = QLabel(Dialog)
        self.label_8.setObjectName(u"label_8")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_8)

        self.tagEdit = QLineEdit(Dialog)
        self.tagEdit.setObjectName(u"tagEdit")
        self.tagEdit.setMaximumSize(QSize(187, 16777215))

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.tagEdit)

        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.xPosSpin = QDoubleSpinBox(Dialog)
        self.xPosSpin.setObjectName(u"xPosSpin")
        self.xPosSpin.setMaximumSize(QSize(90, 16777215))
        self.xPosSpin.setDecimals(6)
        self.xPosSpin.setMinimum(-1000000.000000000000000)
        self.xPosSpin.setMaximum(1000000.000000000000000)

        self.horizontalLayout.addWidget(self.xPosSpin)

        self.yPosSpin = QDoubleSpinBox(Dialog)
        self.yPosSpin.setObjectName(u"yPosSpin")
        self.yPosSpin.setMaximumSize(QSize(90, 16777215))
        self.yPosSpin.setDecimals(6)
        self.yPosSpin.setMinimum(-1000000.000000000000000)
        self.yPosSpin.setMaximum(1000000.000000000000000)

        self.horizontalLayout.addWidget(self.yPosSpin)

        self.zPosSpin = QDoubleSpinBox(Dialog)
        self.zPosSpin.setObjectName(u"zPosSpin")
        self.zPosSpin.setMaximumSize(QSize(90, 16777215))
        self.zPosSpin.setDecimals(6)
        self.zPosSpin.setMinimum(-1000000.000000000000000)
        self.zPosSpin.setMaximum(1000000.000000000000000)

        self.horizontalLayout.addWidget(self.zPosSpin)


        self.formLayout.setLayout(3, QFormLayout.FieldRole, self.horizontalLayout)

        self.label_3 = QLabel(Dialog)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_3)

        self.bearingSpin = QDoubleSpinBox(Dialog)
        self.bearingSpin.setObjectName(u"bearingSpin")
        self.bearingSpin.setMaximumSize(QSize(90, 16777215))
        self.bearingSpin.setDecimals(6)
        self.bearingSpin.setMinimum(-1000000.000000000000000)
        self.bearingSpin.setMaximum(1000000.000000000000000)

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.bearingSpin)

        self.label_11 = QLabel(Dialog)
        self.label_11.setObjectName(u"label_11")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_11)

        self.nameEdit = LocalizedStringLineEdit(Dialog)
        self.nameEdit.setObjectName(u"nameEdit")
        self.nameEdit.setMinimumSize(QSize(0, 23))
        self.nameEdit.setMaximumSize(QSize(219, 16777215))

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.nameEdit)


        self.verticalLayout.addLayout(self.formLayout)

        self.line = QFrame(Dialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.mapNoteEnableCheck = QCheckBox(Dialog)
        self.mapNoteEnableCheck.setObjectName(u"mapNoteEnableCheck")

        self.verticalLayout.addWidget(self.mapNoteEnableCheck)

        self.hasMapNoteCheck = QCheckBox(Dialog)
        self.hasMapNoteCheck.setObjectName(u"hasMapNoteCheck")

        self.verticalLayout.addWidget(self.hasMapNoteCheck)

        self.formLayout_3 = QFormLayout()
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.label_10 = QLabel(Dialog)
        self.label_10.setObjectName(u"label_10")

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label_10)

        self.mapNoteEdit = LocalizedStringLineEdit(Dialog)
        self.mapNoteEdit.setObjectName(u"mapNoteEdit")
        self.mapNoteEdit.setMinimumSize(QSize(0, 23))
        self.mapNoteEdit.setMaximumSize(QSize(219, 16777215))

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.mapNoteEdit)


        self.verticalLayout.addLayout(self.formLayout_3)

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
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Edit Waypoint", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"ResRef:", None))
        self.label_8.setText(QCoreApplication.translate("Dialog", u"Tag:", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Position:", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Bearing:", None))
        self.label_11.setText(QCoreApplication.translate("Dialog", u"Name:", None))
        self.mapNoteEnableCheck.setText(QCoreApplication.translate("Dialog", u"Map Note Enabled", None))
        self.hasMapNoteCheck.setText(QCoreApplication.translate("Dialog", u"Has Map Note", None))
        self.label_10.setText(QCoreApplication.translate("Dialog", u"Map Note:", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
