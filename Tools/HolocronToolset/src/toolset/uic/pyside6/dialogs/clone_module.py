# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'clone_module.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(440, 273)
        self.verticalLayout_6 = QVBoxLayout(Dialog)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.keepDoorsCheckbox = QCheckBox(Dialog)
        self.keepDoorsCheckbox.setObjectName(u"keepDoorsCheckbox")
        self.keepDoorsCheckbox.setChecked(True)

        self.verticalLayout_5.addWidget(self.keepDoorsCheckbox)

        self.keepPlaceablesCheckbox = QCheckBox(Dialog)
        self.keepPlaceablesCheckbox.setObjectName(u"keepPlaceablesCheckbox")
        self.keepPlaceablesCheckbox.setChecked(True)

        self.verticalLayout_5.addWidget(self.keepPlaceablesCheckbox)

        self.keepSoundsCheckbox = QCheckBox(Dialog)
        self.keepSoundsCheckbox.setObjectName(u"keepSoundsCheckbox")
        self.keepSoundsCheckbox.setChecked(True)

        self.verticalLayout_5.addWidget(self.keepSoundsCheckbox)

        self.keepPathingCheckbox = QCheckBox(Dialog)
        self.keepPathingCheckbox.setObjectName(u"keepPathingCheckbox")
        self.keepPathingCheckbox.setChecked(True)

        self.verticalLayout_5.addWidget(self.keepPathingCheckbox)

        self.copyTexturesCheckbox = QCheckBox(Dialog)
        self.copyTexturesCheckbox.setObjectName(u"copyTexturesCheckbox")
        self.copyTexturesCheckbox.setChecked(True)

        self.verticalLayout_5.addWidget(self.copyTexturesCheckbox)

        self.copyLightmapsCheckbox = QCheckBox(Dialog)
        self.copyLightmapsCheckbox.setObjectName(u"copyLightmapsCheckbox")
        self.copyLightmapsCheckbox.setChecked(True)

        self.verticalLayout_5.addWidget(self.copyLightmapsCheckbox)


        self.gridLayout.addLayout(self.verticalLayout_5, 2, 0, 2, 1)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.moduleSelect = QComboBox(Dialog)
        self.moduleSelect.setObjectName(u"moduleSelect")

        self.verticalLayout.addWidget(self.moduleSelect)

        self.moduleRootEdit = QLineEdit(Dialog)
        self.moduleRootEdit.setObjectName(u"moduleRootEdit")
        self.moduleRootEdit.setEnabled(False)

        self.verticalLayout.addWidget(self.moduleRootEdit)


        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 2, 1)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.label_4 = QLabel(Dialog)
        self.label_4.setObjectName(u"label_4")

        self.verticalLayout_4.addWidget(self.label_4)

        self.prefixEdit = QLineEdit(Dialog)
        self.prefixEdit.setObjectName(u"prefixEdit")
        self.prefixEdit.setMaxLength(3)

        self.verticalLayout_4.addWidget(self.prefixEdit)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer)


        self.gridLayout.addLayout(self.verticalLayout_4, 3, 1, 1, 1)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout_2.addWidget(self.label_2)

        self.nameEdit = QLineEdit(Dialog)
        self.nameEdit.setObjectName(u"nameEdit")

        self.verticalLayout_2.addWidget(self.nameEdit)


        self.gridLayout.addLayout(self.verticalLayout_2, 0, 1, 1, 1)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label_3 = QLabel(Dialog)
        self.label_3.setObjectName(u"label_3")

        self.verticalLayout_3.addWidget(self.label_3)

        self.filenameEdit = QLineEdit(Dialog)
        self.filenameEdit.setObjectName(u"filenameEdit")
        self.filenameEdit.setMaxLength(16)

        self.verticalLayout_3.addWidget(self.filenameEdit)


        self.gridLayout.addLayout(self.verticalLayout_3, 1, 1, 2, 1)


        self.verticalLayout_6.addLayout(self.gridLayout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.createButton = QPushButton(Dialog)
        self.createButton.setObjectName(u"createButton")

        self.horizontalLayout.addWidget(self.createButton)

        self.cancelButton = QPushButton(Dialog)
        self.cancelButton.setObjectName(u"cancelButton")

        self.horizontalLayout.addWidget(self.cancelButton)


        self.verticalLayout_6.addLayout(self.horizontalLayout)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Clone Module", None))
        self.keepDoorsCheckbox.setText(QCoreApplication.translate("Dialog", u"Keep Doors", None))
        self.keepPlaceablesCheckbox.setText(QCoreApplication.translate("Dialog", u"Keep Placeables", None))
        self.keepSoundsCheckbox.setText(QCoreApplication.translate("Dialog", u"Keep Sounds", None))
        self.keepPathingCheckbox.setText(QCoreApplication.translate("Dialog", u"Keep Pathing", None))
        self.copyTexturesCheckbox.setText(QCoreApplication.translate("Dialog", u"Copy Textures", None))
        self.copyLightmapsCheckbox.setText(QCoreApplication.translate("Dialog", u"Copy Lightmaps", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Select an existing module:", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"Module prefix:", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Module name:", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Module filename:", None))
        self.createButton.setText(QCoreApplication.translate("Dialog", u"Create", None))
        self.cancelButton.setText(QCoreApplication.translate("Dialog", u"Cancel", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside6
