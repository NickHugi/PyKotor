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
        self.groupBoxFontSettings = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBoxFontSettings.setObjectName(u"groupBoxFontSettings")
        self.verticalLayout_font = QVBoxLayout(self.groupBoxFontSettings)
        self.verticalLayout_font.setObjectName(u"verticalLayout_font")
        self.currentFontLabel = QLabel(self.groupBoxFontSettings)
        self.currentFontLabel.setObjectName(u"currentFontLabel")

        self.verticalLayout_font.addWidget(self.currentFontLabel)

        self.fontButton = QPushButton(self.groupBoxFontSettings)
        self.fontButton.setObjectName(u"fontButton")

        self.verticalLayout_font.addWidget(self.fontButton)


        self.verticalLayout_2.addWidget(self.groupBoxFontSettings)

        self.groupBoxEnvVariables = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBoxEnvVariables.setObjectName(u"groupBoxEnvVariables")
        self.verticalLayout_env = QVBoxLayout(self.groupBoxEnvVariables)
        self.verticalLayout_env.setObjectName(u"verticalLayout_env")
        self.tableWidget = QTableWidget(self.groupBoxEnvVariables)
        if (self.tableWidget.columnCount() < 2):
            self.tableWidget.setColumnCount(2)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        self.tableWidget.setObjectName(u"tableWidget")
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(2)

        self.verticalLayout_env.addWidget(self.tableWidget)

        self.horizontalLayout_buttons = QHBoxLayout()
        self.horizontalLayout_buttons.setObjectName(u"horizontalLayout_buttons")
        self.addButton = QPushButton(self.groupBoxEnvVariables)
        self.addButton.setObjectName(u"addButton")

        self.horizontalLayout_buttons.addWidget(self.addButton)

        self.editButton = QPushButton(self.groupBoxEnvVariables)
        self.editButton.setObjectName(u"editButton")

        self.horizontalLayout_buttons.addWidget(self.editButton)

        self.removeButton = QPushButton(self.groupBoxEnvVariables)
        self.removeButton.setObjectName(u"removeButton")

        self.horizontalLayout_buttons.addWidget(self.removeButton)


        self.verticalLayout_env.addLayout(self.horizontalLayout_buttons)


        self.verticalLayout_2.addWidget(self.groupBoxEnvVariables)

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

        self.groupBoxMiscSettings = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBoxMiscSettings.setObjectName(u"groupBoxMiscSettings")
        self.verticalLayout_misc = QVBoxLayout(self.groupBoxMiscSettings)
        self.verticalLayout_misc.setObjectName(u"verticalLayout_misc")

        self.verticalLayout_2.addWidget(self.groupBoxMiscSettings)

        self.groupBoxAASettings = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBoxAASettings.setObjectName(u"groupBoxAASettings")
        self.verticalLayout_3 = QVBoxLayout(self.groupBoxAASettings)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")

        self.verticalLayout_2.addWidget(self.groupBoxAASettings)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout.addWidget(self.scrollArea)


        self.retranslateUi(ApplicationSettingsWidget)

        QMetaObject.connectSlotsByName(ApplicationSettingsWidget)
    # setupUi

    def retranslateUi(self, ApplicationSettingsWidget):
        ApplicationSettingsWidget.setWindowTitle(QCoreApplication.translate("ApplicationSettingsWidget", u"Application Settings", None))
        self.groupBoxFontSettings.setTitle(QCoreApplication.translate("ApplicationSettingsWidget", u"Global Font Settings", None))
        self.currentFontLabel.setText(QCoreApplication.translate("ApplicationSettingsWidget", u"Current Font: Default", None))
        self.fontButton.setText(QCoreApplication.translate("ApplicationSettingsWidget", u"Select Font...", None))
        self.groupBoxEnvVariables.setTitle(QCoreApplication.translate("ApplicationSettingsWidget", u"Environment Variables", None))
        ___qtablewidgetitem = self.tableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("ApplicationSettingsWidget", u"Variable", None));
        ___qtablewidgetitem1 = self.tableWidget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("ApplicationSettingsWidget", u"Value", None));
        self.addButton.setText(QCoreApplication.translate("ApplicationSettingsWidget", u"Add", None))
        self.editButton.setText(QCoreApplication.translate("ApplicationSettingsWidget", u"Edit", None))
        self.removeButton.setText(QCoreApplication.translate("ApplicationSettingsWidget", u"Remove", None))
        self.resetAttributesButton.setText(QCoreApplication.translate("ApplicationSettingsWidget", u"Reset Attributes", None))
        self.groupBoxMiscSettings.setTitle(QCoreApplication.translate("ApplicationSettingsWidget", u"Miscellaneous Settings", None))
        self.groupBoxAASettings.setTitle(QCoreApplication.translate("ApplicationSettingsWidget", u"Experimental settings (may cause app crashes)", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
