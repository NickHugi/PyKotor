# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'property.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from toolset.gui.widgets.edit.combobox_2da import ComboBox2DA


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(536, 318)
        self.verticalLayout_4 = QVBoxLayout(Dialog)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.propertyEdit = QLineEdit(Dialog)
        self.propertyEdit.setObjectName(u"propertyEdit")
        self.propertyEdit.setEnabled(False)

        self.verticalLayout.addWidget(self.propertyEdit)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout.addWidget(self.label_2)

        self.subpropertyEdit = QLineEdit(Dialog)
        self.subpropertyEdit.setObjectName(u"subpropertyEdit")
        self.subpropertyEdit.setEnabled(False)

        self.verticalLayout.addWidget(self.subpropertyEdit)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.label_3 = QLabel(Dialog)
        self.label_3.setObjectName(u"label_3")

        self.verticalLayout.addWidget(self.label_3)

        self.costEdit = QLineEdit(Dialog)
        self.costEdit.setObjectName(u"costEdit")
        self.costEdit.setEnabled(False)

        self.verticalLayout.addWidget(self.costEdit)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_3)

        self.label_4 = QLabel(Dialog)
        self.label_4.setObjectName(u"label_4")

        self.verticalLayout.addWidget(self.label_4)

        self.parameterEdit = QLineEdit(Dialog)
        self.parameterEdit.setObjectName(u"parameterEdit")
        self.parameterEdit.setEnabled(False)

        self.verticalLayout.addWidget(self.parameterEdit)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_4)

        self.label_7 = QLabel(Dialog)
        self.label_7.setObjectName(u"label_7")

        self.verticalLayout.addWidget(self.label_7)

        self.upgradeSelect = ComboBox2DA(Dialog)
        self.upgradeSelect.setObjectName(u"upgradeSelect")

        self.verticalLayout.addWidget(self.upgradeSelect)


        self.horizontalLayout.addLayout(self.verticalLayout)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_5 = QLabel(Dialog)
        self.label_5.setObjectName(u"label_5")

        self.verticalLayout_2.addWidget(self.label_5)

        self.costList = QListWidget(Dialog)
        self.costList.setObjectName(u"costList")

        self.verticalLayout_2.addWidget(self.costList)

        self.costSelectButton = QPushButton(Dialog)
        self.costSelectButton.setObjectName(u"costSelectButton")

        self.verticalLayout_2.addWidget(self.costSelectButton)


        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label_6 = QLabel(Dialog)
        self.label_6.setObjectName(u"label_6")

        self.verticalLayout_3.addWidget(self.label_6)

        self.parameterList = QListWidget(Dialog)
        self.parameterList.setObjectName(u"parameterList")

        self.verticalLayout_3.addWidget(self.parameterList)

        self.parameterSelectButton = QPushButton(Dialog)
        self.parameterSelectButton.setObjectName(u"parameterSelectButton")

        self.verticalLayout_3.addWidget(self.parameterSelectButton)


        self.horizontalLayout.addLayout(self.verticalLayout_3)

        self.horizontalLayout.setStretch(0, 3)
        self.horizontalLayout.setStretch(1, 4)
        self.horizontalLayout.setStretch(2, 4)

        self.verticalLayout_4.addLayout(self.horizontalLayout)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout_4.addWidget(self.buttonBox)


        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Item Property:", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Item Sub-Property:", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Item Cost Parameter:", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"Parameter 1:", None))
        self.label_7.setText(QCoreApplication.translate("Dialog", u"Upgrade Type:", None))
        self.label_5.setText(QCoreApplication.translate("Dialog", u"Cost Parameter Values:", None))
        self.costSelectButton.setText(QCoreApplication.translate("Dialog", u"Select", None))
        self.label_6.setText(QCoreApplication.translate("Dialog", u"Parameter Values:", None))
        self.parameterSelectButton.setText(QCoreApplication.translate("Dialog", u"Select", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
