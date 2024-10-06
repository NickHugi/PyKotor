
################################################################################
## Form generated from reading UI file 'application.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class Ui_ApplicationSettingsWidget:
    def setupUi(self, ApplicationSettingsWidget):
        if not ApplicationSettingsWidget.objectName():
            ApplicationSettingsWidget.setObjectName("ApplicationSettingsWidget")
        ApplicationSettingsWidget.resize(800, 600)
        self.verticalLayout = QVBoxLayout(ApplicationSettingsWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.resetAttributesButton = QPushButton(ApplicationSettingsWidget)
        self.resetAttributesButton.setObjectName("resetAttributesButton")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(10)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.resetAttributesButton.sizePolicy().hasHeightForWidth())
        self.resetAttributesButton.setSizePolicy(sizePolicy)
        self.resetAttributesButton.setMaximumSize(QSize(16777215, 50))

        self.verticalLayout_4.addWidget(self.resetAttributesButton)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer)


        self.verticalLayout.addLayout(self.verticalLayout_4)

        self.scrollArea = QScrollArea(ApplicationSettingsWidget)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 780, 580))
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.groupBoxFontSettings = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBoxFontSettings.setObjectName("groupBoxFontSettings")
        self.verticalLayout_font = QVBoxLayout(self.groupBoxFontSettings)
        self.verticalLayout_font.setObjectName("verticalLayout_font")
        self.currentFontLabel = QLabel(self.groupBoxFontSettings)
        self.currentFontLabel.setObjectName("currentFontLabel")

        self.verticalLayout_font.addWidget(self.currentFontLabel)

        self.fontButton = QPushButton(self.groupBoxFontSettings)
        self.fontButton.setObjectName("fontButton")

        self.verticalLayout_font.addWidget(self.fontButton)


        self.verticalLayout_2.addWidget(self.groupBoxFontSettings)

        self.groupBoxEnvVariables = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBoxEnvVariables.setObjectName("groupBoxEnvVariables")
        self.verticalLayout_env = QVBoxLayout(self.groupBoxEnvVariables)
        self.verticalLayout_env.setObjectName("verticalLayout_env")
        self.tableWidget = QTableWidget(self.groupBoxEnvVariables)
        if (self.tableWidget.columnCount() < 2):
            self.tableWidget.setColumnCount(2)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(2)

        self.verticalLayout_env.addWidget(self.tableWidget)

        self.horizontalLayout_buttons = QHBoxLayout()
        self.horizontalLayout_buttons.setObjectName("horizontalLayout_buttons")
        self.addButton = QPushButton(self.groupBoxEnvVariables)
        self.addButton.setObjectName("addButton")

        self.horizontalLayout_buttons.addWidget(self.addButton)

        self.editButton = QPushButton(self.groupBoxEnvVariables)
        self.editButton.setObjectName("editButton")

        self.horizontalLayout_buttons.addWidget(self.editButton)

        self.removeButton = QPushButton(self.groupBoxEnvVariables)
        self.removeButton.setObjectName("removeButton")

        self.horizontalLayout_buttons.addWidget(self.removeButton)


        self.verticalLayout_env.addLayout(self.horizontalLayout_buttons)


        self.verticalLayout_2.addWidget(self.groupBoxEnvVariables)

        self.groupBoxMiscSettings = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBoxMiscSettings.setObjectName("groupBoxMiscSettings")
        self.verticalLayout_misc = QVBoxLayout(self.groupBoxMiscSettings)
        self.verticalLayout_misc.setObjectName("verticalLayout_misc")

        self.verticalLayout_2.addWidget(self.groupBoxMiscSettings)

        self.groupBoxAASettings = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBoxAASettings.setObjectName("groupBoxAASettings")
        self.verticalLayout_3 = QVBoxLayout(self.groupBoxAASettings)
        self.verticalLayout_3.setObjectName("verticalLayout_3")

        self.verticalLayout_2.addWidget(self.groupBoxAASettings)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout.addWidget(self.scrollArea)


        self.retranslateUi(ApplicationSettingsWidget)

        QMetaObject.connectSlotsByName(ApplicationSettingsWidget)
    # setupUi

    def retranslateUi(self, ApplicationSettingsWidget):
        ApplicationSettingsWidget.setWindowTitle(QCoreApplication.translate("ApplicationSettingsWidget", "Application Settings", None))
        self.resetAttributesButton.setText(QCoreApplication.translate("ApplicationSettingsWidget", "Reset All on this Page", None))
        self.groupBoxFontSettings.setTitle(QCoreApplication.translate("ApplicationSettingsWidget", "Global Font Settings", None))
        self.currentFontLabel.setText(QCoreApplication.translate("ApplicationSettingsWidget", "Current Font: Default", None))
        self.fontButton.setText(QCoreApplication.translate("ApplicationSettingsWidget", "Select Font...", None))
        self.groupBoxEnvVariables.setTitle(QCoreApplication.translate("ApplicationSettingsWidget", "Environment Variables", None))
        ___qtablewidgetitem = self.tableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("ApplicationSettingsWidget", "Variable", None));
        ___qtablewidgetitem1 = self.tableWidget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("ApplicationSettingsWidget", "Value", None));
        self.addButton.setText(QCoreApplication.translate("ApplicationSettingsWidget", "Add", None))
        self.editButton.setText(QCoreApplication.translate("ApplicationSettingsWidget", "Edit", None))
        self.removeButton.setText(QCoreApplication.translate("ApplicationSettingsWidget", "Remove", None))
        self.groupBoxMiscSettings.setTitle(QCoreApplication.translate("ApplicationSettingsWidget", "Miscellaneous Settings", None))
        self.groupBoxAASettings.setTitle(QCoreApplication.translate("ApplicationSettingsWidget", "Experimental settings (may cause app crashes)", None))
    # retranslateUi

