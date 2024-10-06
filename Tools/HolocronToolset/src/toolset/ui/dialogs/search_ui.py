
################################################################################
## Form generated from reading UI file 'search.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QRadioButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
)


class Ui_Dialog:
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName("Dialog")
        Dialog.resize(310, 391)
        self.verticalLayout_8 = QVBoxLayout(Dialog)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.groupBox = QGroupBox(Dialog)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.installationSelect = QComboBox(self.groupBox)
        self.installationSelect.setObjectName("installationSelect")

        self.gridLayout.addWidget(self.installationSelect, 0, 0, 1, 1)


        self.horizontalLayout.addWidget(self.groupBox)

        self.groupBox_2 = QGroupBox(Dialog)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_2 = QGridLayout(self.groupBox_2)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.searchTextEdit = QLineEdit(self.groupBox_2)
        self.searchTextEdit.setObjectName("searchTextEdit")

        self.gridLayout_2.addWidget(self.searchTextEdit, 0, 0, 1, 1)


        self.horizontalLayout.addWidget(self.groupBox_2)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 1)

        self.verticalLayout_8.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.groupBox_4 = QGroupBox(Dialog)
        self.groupBox_4.setObjectName("groupBox_4")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_4)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.coreCheck = QCheckBox(self.groupBox_4)
        self.coreCheck.setObjectName("coreCheck")
        self.coreCheck.setChecked(True)

        self.verticalLayout_2.addWidget(self.coreCheck)

        self.modulesCheck = QCheckBox(self.groupBox_4)
        self.modulesCheck.setObjectName("modulesCheck")
        self.modulesCheck.setChecked(True)

        self.verticalLayout_2.addWidget(self.modulesCheck)

        self.overrideCheck = QCheckBox(self.groupBox_4)
        self.overrideCheck.setObjectName("overrideCheck")
        self.overrideCheck.setChecked(True)

        self.verticalLayout_2.addWidget(self.overrideCheck)


        self.horizontalLayout_2.addWidget(self.groupBox_4)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.groupBox_3 = QGroupBox(Dialog)
        self.groupBox_3.setObjectName("groupBox_3")
        self.verticalLayout = QVBoxLayout(self.groupBox_3)
        self.verticalLayout.setObjectName("verticalLayout")
        self.caseInsensitiveRadio = QRadioButton(self.groupBox_3)
        self.caseInsensitiveRadio.setObjectName("caseInsensitiveRadio")

        self.verticalLayout.addWidget(self.caseInsensitiveRadio)

        self.caseSensitiveRadio = QRadioButton(self.groupBox_3)
        self.caseSensitiveRadio.setObjectName("caseSensitiveRadio")
        self.caseSensitiveRadio.setChecked(True)

        self.verticalLayout.addWidget(self.caseSensitiveRadio)


        self.verticalLayout_3.addWidget(self.groupBox_3)

        self.groupBox_6 = QGroupBox(Dialog)
        self.groupBox_6.setObjectName("groupBox_6")
        self.gridLayout_3 = QGridLayout(self.groupBox_6)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.filenamesOnlyCheck = QCheckBox(self.groupBox_6)
        self.filenamesOnlyCheck.setObjectName("filenamesOnlyCheck")
        self.filenamesOnlyCheck.setChecked(False)

        self.gridLayout_3.addWidget(self.filenamesOnlyCheck, 0, 0, 1, 1)


        self.verticalLayout_3.addWidget(self.groupBox_6)


        self.horizontalLayout_2.addLayout(self.verticalLayout_3)


        self.verticalLayout_8.addLayout(self.horizontalLayout_2)

        self.groupBox_5 = QGroupBox(Dialog)
        self.groupBox_5.setObjectName("groupBox_5")
        self.gridLayout_4 = QGridLayout(self.groupBox_5)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.selectAllCheck = QCheckBox(self.groupBox_5)
        self.selectAllCheck.setObjectName("selectAllCheck")
        self.selectAllCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.selectAllCheck, 0, 0, 1, 4)

        self.typeARECheck = QCheckBox(self.groupBox_5)
        self.typeARECheck.setObjectName("typeARECheck")
        self.typeARECheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeARECheck, 1, 0, 1, 1)

        self.typeGITCheck = QCheckBox(self.groupBox_5)
        self.typeGITCheck.setObjectName("typeGITCheck")
        self.typeGITCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeGITCheck, 1, 1, 1, 1)

        self.typeIFOCheck = QCheckBox(self.groupBox_5)
        self.typeIFOCheck.setObjectName("typeIFOCheck")
        self.typeIFOCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeIFOCheck, 1, 2, 1, 1)

        self.typeLYTCheck = QCheckBox(self.groupBox_5)
        self.typeLYTCheck.setObjectName("typeLYTCheck")
        self.typeLYTCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeLYTCheck, 1, 3, 1, 1)

        self.typeVISCheck = QCheckBox(self.groupBox_5)
        self.typeVISCheck.setObjectName("typeVISCheck")
        self.typeVISCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeVISCheck, 2, 0, 1, 1)

        self.typeDLGCheck = QCheckBox(self.groupBox_5)
        self.typeDLGCheck.setObjectName("typeDLGCheck")
        self.typeDLGCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeDLGCheck, 2, 1, 1, 1)

        self.typeJRLCheck = QCheckBox(self.groupBox_5)
        self.typeJRLCheck.setObjectName("typeJRLCheck")
        self.typeJRLCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeJRLCheck, 2, 2, 1, 1)

        self.typeUTCCheck = QCheckBox(self.groupBox_5)
        self.typeUTCCheck.setObjectName("typeUTCCheck")
        self.typeUTCCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeUTCCheck, 2, 3, 1, 1)

        self.typeUTDCheck = QCheckBox(self.groupBox_5)
        self.typeUTDCheck.setObjectName("typeUTDCheck")
        self.typeUTDCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeUTDCheck, 3, 0, 1, 1)

        self.typeUTECheck = QCheckBox(self.groupBox_5)
        self.typeUTECheck.setObjectName("typeUTECheck")
        self.typeUTECheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeUTECheck, 3, 1, 1, 1)

        self.typeUTICheck = QCheckBox(self.groupBox_5)
        self.typeUTICheck.setObjectName("typeUTICheck")
        self.typeUTICheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeUTICheck, 3, 2, 1, 1)

        self.typeUTPCheck = QCheckBox(self.groupBox_5)
        self.typeUTPCheck.setObjectName("typeUTPCheck")
        self.typeUTPCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeUTPCheck, 3, 3, 1, 1)

        self.typeUTMCheck = QCheckBox(self.groupBox_5)
        self.typeUTMCheck.setObjectName("typeUTMCheck")
        self.typeUTMCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeUTMCheck, 4, 0, 1, 1)

        self.typeUTWCheck = QCheckBox(self.groupBox_5)
        self.typeUTWCheck.setObjectName("typeUTWCheck")
        self.typeUTWCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeUTWCheck, 4, 1, 1, 1)

        self.typeUTSCheck = QCheckBox(self.groupBox_5)
        self.typeUTSCheck.setObjectName("typeUTSCheck")
        self.typeUTSCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeUTSCheck, 4, 2, 1, 1)

        self.typeUTTCheck = QCheckBox(self.groupBox_5)
        self.typeUTTCheck.setObjectName("typeUTTCheck")
        self.typeUTTCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeUTTCheck, 4, 3, 1, 1)

        self.type2DACheck = QCheckBox(self.groupBox_5)
        self.type2DACheck.setObjectName("type2DACheck")
        self.type2DACheck.setChecked(True)

        self.gridLayout_4.addWidget(self.type2DACheck, 5, 0, 1, 1)

        self.typeNSSCheck = QCheckBox(self.groupBox_5)
        self.typeNSSCheck.setObjectName("typeNSSCheck")
        self.typeNSSCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeNSSCheck, 5, 1, 1, 1)

        self.typeNCSCheck = QCheckBox(self.groupBox_5)
        self.typeNCSCheck.setObjectName("typeNCSCheck")
        self.typeNCSCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeNCSCheck, 5, 2, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_4.addItem(self.verticalSpacer, 5, 3, 1, 1)


        self.verticalLayout_8.addWidget(self.groupBox_5)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName("buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout_8.addWidget(self.buttonBox)


        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", "File Search", None))
        self.groupBox.setTitle(QCoreApplication.translate("Dialog", "Search within", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("Dialog", "String to look for", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("Dialog", "Search in", None))
        self.coreCheck.setText(QCoreApplication.translate("Dialog", "Core", None))
        self.modulesCheck.setText(QCoreApplication.translate("Dialog", "Modules", None))
        self.overrideCheck.setText(QCoreApplication.translate("Dialog", "Override", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("Dialog", "Case", None))
        self.caseInsensitiveRadio.setText(QCoreApplication.translate("Dialog", "Sensitive", None))
        self.caseSensitiveRadio.setText(QCoreApplication.translate("Dialog", "Insensitive", None))
        self.groupBox_6.setTitle(QCoreApplication.translate("Dialog", "Options", None))
        self.filenamesOnlyCheck.setText(QCoreApplication.translate("Dialog", "Filenames only", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("Dialog", "File types to search in", None))
        self.selectAllCheck.setText(QCoreApplication.translate("Dialog", "Select All", None))
        self.typeARECheck.setText(QCoreApplication.translate("Dialog", "ARE", None))
        self.typeGITCheck.setText(QCoreApplication.translate("Dialog", "GIT", None))
        self.typeIFOCheck.setText(QCoreApplication.translate("Dialog", "IFO", None))
        self.typeLYTCheck.setText(QCoreApplication.translate("Dialog", "LYT", None))
        self.typeVISCheck.setText(QCoreApplication.translate("Dialog", "VIS", None))
        self.typeDLGCheck.setText(QCoreApplication.translate("Dialog", "DLG", None))
        self.typeJRLCheck.setText(QCoreApplication.translate("Dialog", "JRL", None))
        self.typeUTCCheck.setText(QCoreApplication.translate("Dialog", "UTC", None))
        self.typeUTDCheck.setText(QCoreApplication.translate("Dialog", "UTD", None))
        self.typeUTECheck.setText(QCoreApplication.translate("Dialog", "UTE", None))
        self.typeUTICheck.setText(QCoreApplication.translate("Dialog", "UTI", None))
        self.typeUTPCheck.setText(QCoreApplication.translate("Dialog", "UTP", None))
        self.typeUTMCheck.setText(QCoreApplication.translate("Dialog", "UTM", None))
        self.typeUTWCheck.setText(QCoreApplication.translate("Dialog", "UTW", None))
        self.typeUTSCheck.setText(QCoreApplication.translate("Dialog", "UTS", None))
        self.typeUTTCheck.setText(QCoreApplication.translate("Dialog", "UTT", None))
        self.type2DACheck.setText(QCoreApplication.translate("Dialog", "2DA", None))
        self.typeNSSCheck.setText(QCoreApplication.translate("Dialog", "NSS", None))
        self.typeNCSCheck.setText(QCoreApplication.translate("Dialog", "NCS", None))
    # retranslateUi

