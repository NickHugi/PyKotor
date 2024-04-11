# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'search.ui'
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
        Dialog.resize(310, 391)
        self.verticalLayout_8 = QVBoxLayout(Dialog)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.groupBox = QGroupBox(Dialog)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout = QGridLayout(self.groupBox)
        self.gridLayout.setObjectName(u"gridLayout")
        self.installationSelect = QComboBox(self.groupBox)
        self.installationSelect.setObjectName(u"installationSelect")

        self.gridLayout.addWidget(self.installationSelect, 0, 0, 1, 1)


        self.horizontalLayout.addWidget(self.groupBox)

        self.groupBox_2 = QGroupBox(Dialog)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.gridLayout_2 = QGridLayout(self.groupBox_2)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.searchTextEdit = QLineEdit(self.groupBox_2)
        self.searchTextEdit.setObjectName(u"searchTextEdit")

        self.gridLayout_2.addWidget(self.searchTextEdit, 0, 0, 1, 1)


        self.horizontalLayout.addWidget(self.groupBox_2)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 1)

        self.verticalLayout_8.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.groupBox_4 = QGroupBox(Dialog)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_4)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.coreCheck = QCheckBox(self.groupBox_4)
        self.coreCheck.setObjectName(u"coreCheck")
        self.coreCheck.setChecked(True)

        self.verticalLayout_2.addWidget(self.coreCheck)

        self.modulesCheck = QCheckBox(self.groupBox_4)
        self.modulesCheck.setObjectName(u"modulesCheck")
        self.modulesCheck.setChecked(True)

        self.verticalLayout_2.addWidget(self.modulesCheck)

        self.overrideCheck = QCheckBox(self.groupBox_4)
        self.overrideCheck.setObjectName(u"overrideCheck")
        self.overrideCheck.setChecked(True)

        self.verticalLayout_2.addWidget(self.overrideCheck)


        self.horizontalLayout_2.addWidget(self.groupBox_4)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.groupBox_3 = QGroupBox(Dialog)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.verticalLayout = QVBoxLayout(self.groupBox_3)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.caseInsensitiveRadio = QRadioButton(self.groupBox_3)
        self.caseInsensitiveRadio.setObjectName(u"caseInsensitiveRadio")

        self.verticalLayout.addWidget(self.caseInsensitiveRadio)

        self.caseSensitiveRadio = QRadioButton(self.groupBox_3)
        self.caseSensitiveRadio.setObjectName(u"caseSensitiveRadio")
        self.caseSensitiveRadio.setChecked(True)

        self.verticalLayout.addWidget(self.caseSensitiveRadio)


        self.verticalLayout_3.addWidget(self.groupBox_3)

        self.groupBox_6 = QGroupBox(Dialog)
        self.groupBox_6.setObjectName(u"groupBox_6")
        self.gridLayout_3 = QGridLayout(self.groupBox_6)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.filenamesOnlyCheck = QCheckBox(self.groupBox_6)
        self.filenamesOnlyCheck.setObjectName(u"filenamesOnlyCheck")
        self.filenamesOnlyCheck.setChecked(False)

        self.gridLayout_3.addWidget(self.filenamesOnlyCheck, 0, 0, 1, 1)


        self.verticalLayout_3.addWidget(self.groupBox_6)


        self.horizontalLayout_2.addLayout(self.verticalLayout_3)


        self.verticalLayout_8.addLayout(self.horizontalLayout_2)

        self.groupBox_5 = QGroupBox(Dialog)
        self.groupBox_5.setObjectName(u"groupBox_5")
        self.horizontalLayout_3 = QHBoxLayout(self.groupBox_5)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.typeARECheck = QCheckBox(self.groupBox_5)
        self.typeARECheck.setObjectName(u"typeARECheck")
        self.typeARECheck.setChecked(True)

        self.verticalLayout_4.addWidget(self.typeARECheck)

        self.typeGITCheck = QCheckBox(self.groupBox_5)
        self.typeGITCheck.setObjectName(u"typeGITCheck")
        self.typeGITCheck.setChecked(True)

        self.verticalLayout_4.addWidget(self.typeGITCheck)

        self.typeIFOCheck = QCheckBox(self.groupBox_5)
        self.typeIFOCheck.setObjectName(u"typeIFOCheck")
        self.typeIFOCheck.setChecked(True)

        self.verticalLayout_4.addWidget(self.typeIFOCheck)

        self.typeDLGCheck = QCheckBox(self.groupBox_5)
        self.typeDLGCheck.setObjectName(u"typeDLGCheck")
        self.typeDLGCheck.setChecked(True)

        self.verticalLayout_4.addWidget(self.typeDLGCheck)

        self.typeJRLCheck = QCheckBox(self.groupBox_5)
        self.typeJRLCheck.setObjectName(u"typeJRLCheck")
        self.typeJRLCheck.setChecked(True)

        self.verticalLayout_4.addWidget(self.typeJRLCheck)


        self.horizontalLayout_3.addLayout(self.verticalLayout_4)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.typeUTCCheck = QCheckBox(self.groupBox_5)
        self.typeUTCCheck.setObjectName(u"typeUTCCheck")
        self.typeUTCCheck.setChecked(True)

        self.verticalLayout_5.addWidget(self.typeUTCCheck)

        self.typeUTDCheck = QCheckBox(self.groupBox_5)
        self.typeUTDCheck.setObjectName(u"typeUTDCheck")
        self.typeUTDCheck.setChecked(True)

        self.verticalLayout_5.addWidget(self.typeUTDCheck)

        self.typeUTECheck = QCheckBox(self.groupBox_5)
        self.typeUTECheck.setObjectName(u"typeUTECheck")
        self.typeUTECheck.setChecked(True)

        self.verticalLayout_5.addWidget(self.typeUTECheck)

        self.typeUTICheck = QCheckBox(self.groupBox_5)
        self.typeUTICheck.setObjectName(u"typeUTICheck")
        self.typeUTICheck.setChecked(True)

        self.verticalLayout_5.addWidget(self.typeUTICheck)

        self.typeUTPCheck = QCheckBox(self.groupBox_5)
        self.typeUTPCheck.setObjectName(u"typeUTPCheck")
        self.typeUTPCheck.setChecked(True)

        self.verticalLayout_5.addWidget(self.typeUTPCheck)


        self.horizontalLayout_3.addLayout(self.verticalLayout_5)

        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.typeUTMCheck = QCheckBox(self.groupBox_5)
        self.typeUTMCheck.setObjectName(u"typeUTMCheck")
        self.typeUTMCheck.setChecked(True)

        self.verticalLayout_6.addWidget(self.typeUTMCheck)

        self.typeUTWCheck = QCheckBox(self.groupBox_5)
        self.typeUTWCheck.setObjectName(u"typeUTWCheck")
        self.typeUTWCheck.setChecked(True)

        self.verticalLayout_6.addWidget(self.typeUTWCheck)

        self.typeUTSCheck = QCheckBox(self.groupBox_5)
        self.typeUTSCheck.setObjectName(u"typeUTSCheck")
        self.typeUTSCheck.setChecked(True)

        self.verticalLayout_6.addWidget(self.typeUTSCheck)

        self.typeUTTCheck = QCheckBox(self.groupBox_5)
        self.typeUTTCheck.setObjectName(u"typeUTTCheck")
        self.typeUTTCheck.setChecked(True)

        self.verticalLayout_6.addWidget(self.typeUTTCheck)

        self.type2DACheck = QCheckBox(self.groupBox_5)
        self.type2DACheck.setObjectName(u"type2DACheck")
        self.type2DACheck.setChecked(True)

        self.verticalLayout_6.addWidget(self.type2DACheck)


        self.horizontalLayout_3.addLayout(self.verticalLayout_6)

        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.typeNSSCheck = QCheckBox(self.groupBox_5)
        self.typeNSSCheck.setObjectName(u"typeNSSCheck")
        self.typeNSSCheck.setChecked(True)

        self.verticalLayout_7.addWidget(self.typeNSSCheck)

        self.typeNCSCheck = QCheckBox(self.groupBox_5)
        self.typeNCSCheck.setObjectName(u"typeNCSCheck")
        self.typeNCSCheck.setChecked(True)

        self.verticalLayout_7.addWidget(self.typeNCSCheck)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_7.addItem(self.verticalSpacer)


        self.horizontalLayout_3.addLayout(self.verticalLayout_7)


        self.verticalLayout_8.addWidget(self.groupBox_5)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout_8.addWidget(self.buttonBox)


        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"File Search", None))
        self.groupBox.setTitle(QCoreApplication.translate("Dialog", u"Search within", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("Dialog", u"String to look for", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("Dialog", u"Search in", None))
        self.coreCheck.setText(QCoreApplication.translate("Dialog", u"Core", None))
        self.modulesCheck.setText(QCoreApplication.translate("Dialog", u"Modules", None))
        self.overrideCheck.setText(QCoreApplication.translate("Dialog", u"Override", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("Dialog", u"Case", None))
        self.caseInsensitiveRadio.setText(QCoreApplication.translate("Dialog", u"Sensitive", None))
        self.caseSensitiveRadio.setText(QCoreApplication.translate("Dialog", u"Insensitive", None))
        self.groupBox_6.setTitle(QCoreApplication.translate("Dialog", u"Options", None))
        self.filenamesOnlyCheck.setText(QCoreApplication.translate("Dialog", u"Filenames only", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("Dialog", u"File types to search in", None))
        self.typeARECheck.setText(QCoreApplication.translate("Dialog", u"ARE", None))
        self.typeGITCheck.setText(QCoreApplication.translate("Dialog", u"GIT", None))
        self.typeIFOCheck.setText(QCoreApplication.translate("Dialog", u"IFO", None))
        self.typeDLGCheck.setText(QCoreApplication.translate("Dialog", u"DLG", None))
        self.typeJRLCheck.setText(QCoreApplication.translate("Dialog", u"JRL", None))
        self.typeUTCCheck.setText(QCoreApplication.translate("Dialog", u"UTC", None))
        self.typeUTDCheck.setText(QCoreApplication.translate("Dialog", u"UTD", None))
        self.typeUTECheck.setText(QCoreApplication.translate("Dialog", u"UTE", None))
        self.typeUTICheck.setText(QCoreApplication.translate("Dialog", u"UTI", None))
        self.typeUTPCheck.setText(QCoreApplication.translate("Dialog", u"UTP", None))
        self.typeUTMCheck.setText(QCoreApplication.translate("Dialog", u"UTM", None))
        self.typeUTWCheck.setText(QCoreApplication.translate("Dialog", u"UTW", None))
        self.typeUTSCheck.setText(QCoreApplication.translate("Dialog", u"UTS", None))
        self.typeUTTCheck.setText(QCoreApplication.translate("Dialog", u"UTT", None))
        self.type2DACheck.setText(QCoreApplication.translate("Dialog", u"2DA", None))
        self.typeNSSCheck.setText(QCoreApplication.translate("Dialog", u"NSS", None))
        self.typeNCSCheck.setText(QCoreApplication.translate("Dialog", u"NCS", None))
    # retranslateUi

