# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'camera.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel,
    QSizePolicy, QSpacerItem, QSpinBox, QVBoxLayout,
    QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(464, 222)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
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

        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.xPosSpin = QDoubleSpinBox(Dialog)
        self.xPosSpin.setObjectName(u"xPosSpin")
        self.xPosSpin.setMaximumSize(QSize(90, 16777215))
        self.xPosSpin.setDecimals(6)
        self.xPosSpin.setMinimum(-100000.000000000000000)
        self.xPosSpin.setMaximum(100000.000000000000000)

        self.horizontalLayout.addWidget(self.xPosSpin)

        self.yPosSpin = QDoubleSpinBox(Dialog)
        self.yPosSpin.setObjectName(u"yPosSpin")
        self.yPosSpin.setMaximumSize(QSize(90, 16777215))
        self.yPosSpin.setDecimals(6)
        self.yPosSpin.setMinimum(-100000.000000000000000)
        self.yPosSpin.setMaximum(100000.000000000000000)

        self.horizontalLayout.addWidget(self.yPosSpin)

        self.zPosSpin = QDoubleSpinBox(Dialog)
        self.zPosSpin.setObjectName(u"zPosSpin")
        self.zPosSpin.setMaximumSize(QSize(90, 16777215))
        self.zPosSpin.setDecimals(6)
        self.zPosSpin.setMinimum(-100000.000000000000000)
        self.zPosSpin.setMaximum(100000.000000000000000)

        self.horizontalLayout.addWidget(self.zPosSpin)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.formLayout.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout)

        self.label_3 = QLabel(Dialog)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_3)

        self.label_4 = QLabel(Dialog)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_4)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.xOrientSpin = QDoubleSpinBox(Dialog)
        self.xOrientSpin.setObjectName(u"xOrientSpin")
        self.xOrientSpin.setMaximumSize(QSize(90, 16777215))
        self.xOrientSpin.setDecimals(6)
        self.xOrientSpin.setMinimum(-1000000.000000000000000)
        self.xOrientSpin.setMaximum(1000000.000000000000000)

        self.horizontalLayout_2.addWidget(self.xOrientSpin)

        self.yOrientSpin = QDoubleSpinBox(Dialog)
        self.yOrientSpin.setObjectName(u"yOrientSpin")
        self.yOrientSpin.setMaximumSize(QSize(90, 16777215))
        self.yOrientSpin.setDecimals(6)
        self.yOrientSpin.setMinimum(-1000000.000000000000000)
        self.yOrientSpin.setMaximum(1000000.000000000000000)

        self.horizontalLayout_2.addWidget(self.yOrientSpin)

        self.zOrientSpin = QDoubleSpinBox(Dialog)
        self.zOrientSpin.setObjectName(u"zOrientSpin")
        self.zOrientSpin.setMaximumSize(QSize(90, 16777215))
        self.zOrientSpin.setDecimals(6)
        self.zOrientSpin.setMinimum(-1000000.000000000000000)
        self.zOrientSpin.setMaximum(1000000.000000000000000)

        self.horizontalLayout_2.addWidget(self.zOrientSpin)

        self.wOrientSpin = QDoubleSpinBox(Dialog)
        self.wOrientSpin.setObjectName(u"wOrientSpin")
        self.wOrientSpin.setMaximumSize(QSize(90, 16777215))
        self.wOrientSpin.setDecimals(6)
        self.wOrientSpin.setMinimum(-1000000.000000000000000)
        self.wOrientSpin.setMaximum(1000000.000000000000000)

        self.horizontalLayout_2.addWidget(self.wOrientSpin)


        self.formLayout.setLayout(2, QFormLayout.FieldRole, self.horizontalLayout_2)

        self.cameraIdSpin = QSpinBox(Dialog)
        self.cameraIdSpin.setObjectName(u"cameraIdSpin")
        self.cameraIdSpin.setMaximumSize(QSize(90, 16777215))
        self.cameraIdSpin.setMaximum(255)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.cameraIdSpin)

        self.fovSpin = QDoubleSpinBox(Dialog)
        self.fovSpin.setObjectName(u"fovSpin")
        self.fovSpin.setMaximumSize(QSize(90, 16777215))
        self.fovSpin.setDecimals(6)
        self.fovSpin.setMinimum(20.000000000000000)
        self.fovSpin.setMaximum(200.000000000000000)
        self.fovSpin.setValue(50.000000000000000)

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.fovSpin)

        self.label_5 = QLabel(Dialog)
        self.label_5.setObjectName(u"label_5")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_5)

        self.label_6 = QLabel(Dialog)
        self.label_6.setObjectName(u"label_6")

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.label_6)

        self.label_7 = QLabel(Dialog)
        self.label_7.setObjectName(u"label_7")

        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.label_7)

        self.pitchSpin = QDoubleSpinBox(Dialog)
        self.pitchSpin.setObjectName(u"pitchSpin")
        self.pitchSpin.setMaximumSize(QSize(90, 16777215))
        self.pitchSpin.setDecimals(6)
        self.pitchSpin.setMaximum(360.000000000000000)

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.pitchSpin)

        self.micRangeSpin = QDoubleSpinBox(Dialog)
        self.micRangeSpin.setObjectName(u"micRangeSpin")
        self.micRangeSpin.setMaximumSize(QSize(90, 16777215))
        self.micRangeSpin.setDecimals(6)
        self.micRangeSpin.setMaximum(100000.000000000000000)

        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.micRangeSpin)

        self.heightSpin = QDoubleSpinBox(Dialog)
        self.heightSpin.setObjectName(u"heightSpin")
        self.heightSpin.setMaximumSize(QSize(90, 16777215))
        self.heightSpin.setDecimals(6)
        self.heightSpin.setMinimum(-100000.000000000000000)
        self.heightSpin.setMaximum(100000.000000000000000)

        self.formLayout.setWidget(6, QFormLayout.FieldRole, self.heightSpin)


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
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Edit Camera", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Camera ID:", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Position:", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Orientation:", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"FOV:", None))
        self.label_5.setText(QCoreApplication.translate("Dialog", u"Pitch:", None))
        self.label_6.setText(QCoreApplication.translate("Dialog", u"Mic Range:", None))
        self.label_7.setText(QCoreApplication.translate("Dialog", u"Height:", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside6
