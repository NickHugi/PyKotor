# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'sound.ui'
##
## Created by: Qt User Interface Compiler version 6.6.1
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QSizePolicy, QVBoxLayout, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(352, 97)
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

        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

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


        self.formLayout.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout)


        self.verticalLayout.addLayout(self.formLayout)

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
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Edit Sound", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"ResRef:", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Position:", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside6
