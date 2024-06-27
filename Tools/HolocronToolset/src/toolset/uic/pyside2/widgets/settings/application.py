# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'application.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_ApplicationSettingsWidget(object):
    def setupUi(self, ApplicationSettingsWidget):
        if not ApplicationSettingsWidget.objectName():
            ApplicationSettingsWidget.setObjectName(u"ApplicationSettingsWidget")
        ApplicationSettingsWidget.resize(800, 600)
        self.verticalLayout = QVBoxLayout(ApplicationSettingsWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.scrollArea = QScrollArea(ApplicationSettingsWidget)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 780, 580))
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.groupBoxAASettings = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBoxAASettings.setObjectName(u"groupBoxAASettings")
        self.verticalLayout_3 = QVBoxLayout(self.groupBoxAASettings)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")

        self.verticalLayout_2.addWidget(self.groupBoxAASettings)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.resetAttributesButton = QPushButton(self.scrollAreaWidgetContents)
        self.resetAttributesButton.setObjectName(u"resetAttributesButton")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(10)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.resetAttributesButton.sizePolicy().hasHeightForWidth())
        self.resetAttributesButton.setSizePolicy(sizePolicy)
        self.resetAttributesButton.setMaximumSize(QSize(16777215, 50))

        self.verticalLayout_4.addWidget(self.resetAttributesButton)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer)


        self.verticalLayout_2.addLayout(self.verticalLayout_4)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout.addWidget(self.scrollArea)


        self.retranslateUi(ApplicationSettingsWidget)

        QMetaObject.connectSlotsByName(ApplicationSettingsWidget)
    # setupUi

    def retranslateUi(self, ApplicationSettingsWidget):
        ApplicationSettingsWidget.setWindowTitle(QCoreApplication.translate("ApplicationSettingsWidget", u"Application Settings", None))
        self.groupBoxAASettings.setTitle(QCoreApplication.translate("ApplicationSettingsWidget", u"Experimental settings (may cause app crashes)", None))
        self.resetAttributesButton.setText(QCoreApplication.translate("ApplicationSettingsWidget", u"Reset Attributes", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
