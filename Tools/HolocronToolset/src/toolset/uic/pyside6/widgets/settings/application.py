# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'application.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QScrollArea, QSizePolicy,
    QSpinBox, QVBoxLayout, QWidget)

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
        self.AA_ImmediateWidgetCreationCheckBox = QCheckBox(self.groupBoxAASettings)
        self.AA_ImmediateWidgetCreationCheckBox.setObjectName(u"AA_ImmediateWidgetCreationCheckBox")

        self.verticalLayout_3.addWidget(self.AA_ImmediateWidgetCreationCheckBox)


        self.verticalLayout_2.addWidget(self.groupBoxAASettings)

        self.groupBoxCacheSettings = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBoxCacheSettings.setObjectName(u"groupBoxCacheSettings")
        self.formLayoutCacheSettings = QFormLayout(self.groupBoxCacheSettings)
        self.formLayoutCacheSettings.setObjectName(u"formLayoutCacheSettings")
        self.labelCacheSize = QLabel(self.groupBoxCacheSettings)
        self.labelCacheSize.setObjectName(u"labelCacheSize")

        self.formLayoutCacheSettings.setWidget(0, QFormLayout.LabelRole, self.labelCacheSize)

        self.cacheSizeSpinBox = QSpinBox(self.groupBoxCacheSettings)
        self.cacheSizeSpinBox.setObjectName(u"cacheSizeSpinBox")

        self.formLayoutCacheSettings.setWidget(0, QFormLayout.FieldRole, self.cacheSizeSpinBox)

        self.labelCacheDirectory = QLabel(self.groupBoxCacheSettings)
        self.labelCacheDirectory.setObjectName(u"labelCacheDirectory")

        self.formLayoutCacheSettings.setWidget(1, QFormLayout.LabelRole, self.labelCacheDirectory)

        self.cacheDirectoryLineEdit = QLineEdit(self.groupBoxCacheSettings)
        self.cacheDirectoryLineEdit.setObjectName(u"cacheDirectoryLineEdit")

        self.formLayoutCacheSettings.setWidget(1, QFormLayout.FieldRole, self.cacheDirectoryLineEdit)


        self.verticalLayout_2.addWidget(self.groupBoxCacheSettings)

        self.groupBoxEnvironmentVariables = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBoxEnvironmentVariables.setObjectName(u"groupBoxEnvironmentVariables")
        self.verticalLayoutEnvironmentVariables = QVBoxLayout(self.groupBoxEnvironmentVariables)
        self.verticalLayoutEnvironmentVariables.setObjectName(u"verticalLayoutEnvironmentVariables")
        self.environmentVariablesListWidget = QListWidget(self.groupBoxEnvironmentVariables)
        self.environmentVariablesListWidget.setObjectName(u"environmentVariablesListWidget")

        self.verticalLayoutEnvironmentVariables.addWidget(self.environmentVariablesListWidget)


        self.verticalLayout_2.addWidget(self.groupBoxEnvironmentVariables)

        self.groupBoxFilePaths = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBoxFilePaths.setObjectName(u"groupBoxFilePaths")
        self.formLayoutFilePaths = QFormLayout(self.groupBoxFilePaths)
        self.formLayoutFilePaths.setObjectName(u"formLayoutFilePaths")
        self.labelLogFilePath = QLabel(self.groupBoxFilePaths)
        self.labelLogFilePath.setObjectName(u"labelLogFilePath")

        self.formLayoutFilePaths.setWidget(0, QFormLayout.LabelRole, self.labelLogFilePath)

        self.logFilePathLineEdit = QLineEdit(self.groupBoxFilePaths)
        self.logFilePathLineEdit.setObjectName(u"logFilePathLineEdit")

        self.formLayoutFilePaths.setWidget(0, QFormLayout.FieldRole, self.logFilePathLineEdit)

        self.labelTempFilePath = QLabel(self.groupBoxFilePaths)
        self.labelTempFilePath.setObjectName(u"labelTempFilePath")

        self.formLayoutFilePaths.setWidget(1, QFormLayout.LabelRole, self.labelTempFilePath)

        self.tempFilePathLineEdit = QLineEdit(self.groupBoxFilePaths)
        self.tempFilePathLineEdit.setObjectName(u"tempFilePathLineEdit")

        self.formLayoutFilePaths.setWidget(1, QFormLayout.FieldRole, self.tempFilePathLineEdit)


        self.verticalLayout_2.addWidget(self.groupBoxFilePaths)

        self.groupBoxPerformanceSettings = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBoxPerformanceSettings.setObjectName(u"groupBoxPerformanceSettings")
        self.formLayoutPerformanceSettings = QFormLayout(self.groupBoxPerformanceSettings)
        self.formLayoutPerformanceSettings.setObjectName(u"formLayoutPerformanceSettings")
        self.labelMaxThreads = QLabel(self.groupBoxPerformanceSettings)
        self.labelMaxThreads.setObjectName(u"labelMaxThreads")

        self.formLayoutPerformanceSettings.setWidget(0, QFormLayout.LabelRole, self.labelMaxThreads)

        self.maxThreadsSpinBox = QSpinBox(self.groupBoxPerformanceSettings)
        self.maxThreadsSpinBox.setObjectName(u"maxThreadsSpinBox")

        self.formLayoutPerformanceSettings.setWidget(0, QFormLayout.FieldRole, self.maxThreadsSpinBox)


        self.verticalLayout_2.addWidget(self.groupBoxPerformanceSettings)

        self.horizontalLayoutButtons = QHBoxLayout()
        self.horizontalLayoutButtons.setObjectName(u"horizontalLayoutButtons")
        self.resetAttributesButton = QPushButton(self.scrollAreaWidgetContents)
        self.resetAttributesButton.setObjectName(u"resetAttributesButton")

        self.horizontalLayoutButtons.addWidget(self.resetAttributesButton)

        self.resetCacheSettingsButton = QPushButton(self.scrollAreaWidgetContents)
        self.resetCacheSettingsButton.setObjectName(u"resetCacheSettingsButton")

        self.horizontalLayoutButtons.addWidget(self.resetCacheSettingsButton)

        self.resetEnvironmentVariablesButton = QPushButton(self.scrollAreaWidgetContents)
        self.resetEnvironmentVariablesButton.setObjectName(u"resetEnvironmentVariablesButton")

        self.horizontalLayoutButtons.addWidget(self.resetEnvironmentVariablesButton)

        self.resetFilePathsButton = QPushButton(self.scrollAreaWidgetContents)
        self.resetFilePathsButton.setObjectName(u"resetFilePathsButton")

        self.horizontalLayoutButtons.addWidget(self.resetFilePathsButton)

        self.resetPerformanceSettingsButton = QPushButton(self.scrollAreaWidgetContents)
        self.resetPerformanceSettingsButton.setObjectName(u"resetPerformanceSettingsButton")

        self.horizontalLayoutButtons.addWidget(self.resetPerformanceSettingsButton)


        self.verticalLayout_2.addLayout(self.horizontalLayoutButtons)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout.addWidget(self.scrollArea)


        self.retranslateUi(ApplicationSettingsWidget)

        QMetaObject.connectSlotsByName(ApplicationSettingsWidget)
    # setupUi

    def retranslateUi(self, ApplicationSettingsWidget):
        ApplicationSettingsWidget.setWindowTitle(QCoreApplication.translate("ApplicationSettingsWidget", u"Application Settings", None))
        self.groupBoxAASettings.setTitle(QCoreApplication.translate("ApplicationSettingsWidget", u"AA Settings", None))
        self.AA_ImmediateWidgetCreationCheckBox.setText(QCoreApplication.translate("ApplicationSettingsWidget", u"Immediate Widget Creation", None))
        self.groupBoxCacheSettings.setTitle(QCoreApplication.translate("ApplicationSettingsWidget", u"Cache Settings", None))
        self.labelCacheSize.setText(QCoreApplication.translate("ApplicationSettingsWidget", u"Cache Size:", None))
        self.labelCacheDirectory.setText(QCoreApplication.translate("ApplicationSettingsWidget", u"Cache Directory:", None))
        self.groupBoxEnvironmentVariables.setTitle(QCoreApplication.translate("ApplicationSettingsWidget", u"Environment Variables", None))
        self.groupBoxFilePaths.setTitle(QCoreApplication.translate("ApplicationSettingsWidget", u"File Paths", None))
        self.labelLogFilePath.setText(QCoreApplication.translate("ApplicationSettingsWidget", u"Log File Path:", None))
        self.labelTempFilePath.setText(QCoreApplication.translate("ApplicationSettingsWidget", u"Temp File Path:", None))
        self.groupBoxPerformanceSettings.setTitle(QCoreApplication.translate("ApplicationSettingsWidget", u"Performance Settings", None))
        self.labelMaxThreads.setText(QCoreApplication.translate("ApplicationSettingsWidget", u"Max Threads:", None))
        self.resetAttributesButton.setText(QCoreApplication.translate("ApplicationSettingsWidget", u"Reset Attributes", None))
        self.resetCacheSettingsButton.setText(QCoreApplication.translate("ApplicationSettingsWidget", u"Reset Cache Settings", None))
        self.resetEnvironmentVariablesButton.setText(QCoreApplication.translate("ApplicationSettingsWidget", u"Reset Environment Variables", None))
        self.resetFilePathsButton.setText(QCoreApplication.translate("ApplicationSettingsWidget", u"Reset File Paths", None))
        self.resetPerformanceSettingsButton.setText(QCoreApplication.translate("ApplicationSettingsWidget", u"Reset Performance Settings", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside6
