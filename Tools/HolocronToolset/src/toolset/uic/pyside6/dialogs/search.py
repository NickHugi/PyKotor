# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'search.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QGridLayout, QGroupBox,
    QHBoxLayout, QLineEdit, QRadioButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

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
        self.gridLayout_4 = QGridLayout(self.groupBox_5)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.selectAllCheck = QCheckBox(self.groupBox_5)
        self.selectAllCheck.setObjectName(u"selectAllCheck")
        self.selectAllCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.selectAllCheck, 0, 0, 1, 4)

        self.typeARECheck = QCheckBox(self.groupBox_5)
        self.typeARECheck.setObjectName(u"typeARECheck")
        self.typeARECheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeARECheck, 1, 0, 1, 1)

        self.typeGITCheck = QCheckBox(self.groupBox_5)
        self.typeGITCheck.setObjectName(u"typeGITCheck")
        self.typeGITCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeGITCheck, 1, 1, 1, 1)

        self.typeIFOCheck = QCheckBox(self.groupBox_5)
        self.typeIFOCheck.setObjectName(u"typeIFOCheck")
        self.typeIFOCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeIFOCheck, 1, 2, 1, 1)

        self.typeLYTCheck = QCheckBox(self.groupBox_5)
        self.typeLYTCheck.setObjectName(u"typeLYTCheck")
        self.typeLYTCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeLYTCheck, 1, 3, 1, 1)

        self.typeVISCheck = QCheckBox(self.groupBox_5)
        self.typeVISCheck.setObjectName(u"typeVISCheck")
        self.typeVISCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeVISCheck, 2, 0, 1, 1)

        self.typeDLGCheck = QCheckBox(self.groupBox_5)
        self.typeDLGCheck.setObjectName(u"typeDLGCheck")
        self.typeDLGCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeDLGCheck, 2, 1, 1, 1)

        self.typeJRLCheck = QCheckBox(self.groupBox_5)
        self.typeJRLCheck.setObjectName(u"typeJRLCheck")
        self.typeJRLCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeJRLCheck, 2, 2, 1, 1)

        self.typeUTCCheck = QCheckBox(self.groupBox_5)
        self.typeUTCCheck.setObjectName(u"typeUTCCheck")
        self.typeUTCCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeUTCCheck, 2, 3, 1, 1)

        self.typeUTDCheck = QCheckBox(self.groupBox_5)
        self.typeUTDCheck.setObjectName(u"typeUTDCheck")
        self.typeUTDCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeUTDCheck, 3, 0, 1, 1)

        self.typeUTECheck = QCheckBox(self.groupBox_5)
        self.typeUTECheck.setObjectName(u"typeUTECheck")
        self.typeUTECheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeUTECheck, 3, 1, 1, 1)

        self.typeUTICheck = QCheckBox(self.groupBox_5)
        self.typeUTICheck.setObjectName(u"typeUTICheck")
        self.typeUTICheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeUTICheck, 3, 2, 1, 1)

        self.typeUTPCheck = QCheckBox(self.groupBox_5)
        self.typeUTPCheck.setObjectName(u"typeUTPCheck")
        self.typeUTPCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeUTPCheck, 3, 3, 1, 1)

        self.typeUTMCheck = QCheckBox(self.groupBox_5)
        self.typeUTMCheck.setObjectName(u"typeUTMCheck")
        self.typeUTMCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeUTMCheck, 4, 0, 1, 1)

        self.typeUTWCheck = QCheckBox(self.groupBox_5)
        self.typeUTWCheck.setObjectName(u"typeUTWCheck")
        self.typeUTWCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeUTWCheck, 4, 1, 1, 1)

        self.typeUTSCheck = QCheckBox(self.groupBox_5)
        self.typeUTSCheck.setObjectName(u"typeUTSCheck")
        self.typeUTSCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeUTSCheck, 4, 2, 1, 1)

        self.typeUTTCheck = QCheckBox(self.groupBox_5)
        self.typeUTTCheck.setObjectName(u"typeUTTCheck")
        self.typeUTTCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeUTTCheck, 4, 3, 1, 1)

        self.type2DACheck = QCheckBox(self.groupBox_5)
        self.type2DACheck.setObjectName(u"type2DACheck")
        self.type2DACheck.setChecked(True)

        self.gridLayout_4.addWidget(self.type2DACheck, 5, 0, 1, 1)

        self.typeNSSCheck = QCheckBox(self.groupBox_5)
        self.typeNSSCheck.setObjectName(u"typeNSSCheck")
        self.typeNSSCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeNSSCheck, 5, 1, 1, 1)

        self.typeNCSCheck = QCheckBox(self.groupBox_5)
        self.typeNCSCheck.setObjectName(u"typeNCSCheck")
        self.typeNCSCheck.setChecked(True)

        self.gridLayout_4.addWidget(self.typeNCSCheck, 5, 2, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_4.addItem(self.verticalSpacer, 5, 3, 1, 1)


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
        self.selectAllCheck.setText(QCoreApplication.translate("Dialog", u"Select All", None))
        self.typeARECheck.setText(QCoreApplication.translate("Dialog", u"ARE", None))
        self.typeGITCheck.setText(QCoreApplication.translate("Dialog", u"GIT", None))
        self.typeIFOCheck.setText(QCoreApplication.translate("Dialog", u"IFO", None))
        self.typeLYTCheck.setText(QCoreApplication.translate("Dialog", u"LYT", None))
        self.typeVISCheck.setText(QCoreApplication.translate("Dialog", u"VIS", None))
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


from toolset.rcc import resources_rc_pyside6
