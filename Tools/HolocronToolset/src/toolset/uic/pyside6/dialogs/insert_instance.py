# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'insert_instance.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QRadioButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

from toolset.gui.widgets.renderer.model import ModelRenderer

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(800, 600)
        self.horizontalLayout = QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.leftPanelLayout = QVBoxLayout()
        self.leftPanelLayout.setObjectName(u"leftPanelLayout")
        self.previewGroup = QGroupBox(Dialog)
        self.previewGroup.setObjectName(u"previewGroup")
        self.previewLayout = QVBoxLayout(self.previewGroup)
        self.previewLayout.setObjectName(u"previewLayout")
        self.previewRenderer = ModelRenderer(self.previewGroup)
        self.previewRenderer.setObjectName(u"previewRenderer")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.previewRenderer.sizePolicy().hasHeightForWidth())
        self.previewRenderer.setSizePolicy(sizePolicy)
        self.previewRenderer.setMinimumSize(QSize(250, 250))
        self.previewRenderer.setMouseTracking(True)
        self.previewRenderer.setFocusPolicy(Qt.StrongFocus)

        self.previewLayout.addWidget(self.previewRenderer)


        self.leftPanelLayout.addWidget(self.previewGroup)

        self.infoGroup = QGroupBox(Dialog)
        self.infoGroup.setObjectName(u"infoGroup")
        self.infoLayout = QVBoxLayout(self.infoGroup)
        self.infoLayout.setObjectName(u"infoLayout")
        self.dynamicTextLabel = QLabel(self.infoGroup)
        self.dynamicTextLabel.setObjectName(u"dynamicTextLabel")
        self.dynamicTextLabel.setWordWrap(True)

        self.infoLayout.addWidget(self.dynamicTextLabel)

        self.staticTextLabel = QLabel(self.infoGroup)
        self.staticTextLabel.setObjectName(u"staticTextLabel")
        self.staticTextLabel.setWordWrap(True)

        self.infoLayout.addWidget(self.staticTextLabel)


        self.leftPanelLayout.addWidget(self.infoGroup)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.leftPanelLayout.addItem(self.verticalSpacer)


        self.horizontalLayout.addLayout(self.leftPanelLayout)

        self.rightPanelLayout = QVBoxLayout()
        self.rightPanelLayout.setObjectName(u"rightPanelLayout")
        self.settingsGroup = QGroupBox(Dialog)
        self.settingsGroup.setObjectName(u"settingsGroup")
        self.formLayout = QFormLayout(self.settingsGroup)
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(self.settingsGroup)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.resrefEdit = QLineEdit(self.settingsGroup)
        self.resrefEdit.setObjectName(u"resrefEdit")
        self.resrefEdit.setEnabled(False)
        self.resrefEdit.setMaxLength(16)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.resrefEdit)

        self.label_2 = QLabel(self.settingsGroup)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.locationSelect = QComboBox(self.settingsGroup)
        self.locationSelect.setObjectName(u"locationSelect")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.locationSelect)


        self.rightPanelLayout.addWidget(self.settingsGroup)

        self.resourceTypeGroup = QGroupBox(Dialog)
        self.resourceTypeGroup.setObjectName(u"resourceTypeGroup")
        self.horizontalLayout_2 = QHBoxLayout(self.resourceTypeGroup)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.reuseResourceRadio = QRadioButton(self.resourceTypeGroup)
        self.reuseResourceRadio.setObjectName(u"reuseResourceRadio")
        self.reuseResourceRadio.setChecked(True)

        self.horizontalLayout_2.addWidget(self.reuseResourceRadio)

        self.copyResourceRadio = QRadioButton(self.resourceTypeGroup)
        self.copyResourceRadio.setObjectName(u"copyResourceRadio")

        self.horizontalLayout_2.addWidget(self.copyResourceRadio)

        self.createResourceRadio = QRadioButton(self.resourceTypeGroup)
        self.createResourceRadio.setObjectName(u"createResourceRadio")

        self.horizontalLayout_2.addWidget(self.createResourceRadio)


        self.rightPanelLayout.addWidget(self.resourceTypeGroup)

        self.resourceListGroup = QGroupBox(Dialog)
        self.resourceListGroup.setObjectName(u"resourceListGroup")
        self.verticalLayout_2 = QVBoxLayout(self.resourceListGroup)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.resourceFilter = QLineEdit(self.resourceListGroup)
        self.resourceFilter.setObjectName(u"resourceFilter")
        self.resourceFilter.setClearButtonEnabled(True)

        self.verticalLayout_2.addWidget(self.resourceFilter)

        self.resourceList = QListWidget(self.resourceListGroup)
        self.resourceList.setObjectName(u"resourceList")
        self.resourceList.setSortingEnabled(True)
        self.resourceList.setAlternatingRowColors(True)

        self.verticalLayout_2.addWidget(self.resourceList)


        self.rightPanelLayout.addWidget(self.resourceListGroup)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.rightPanelLayout.addWidget(self.buttonBox)


        self.horizontalLayout.addLayout(self.rightPanelLayout)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 2)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Insert Instance", None))
        self.previewGroup.setTitle(QCoreApplication.translate("Dialog", u"Preview", None))
        self.infoGroup.setTitle(QCoreApplication.translate("Dialog", u"Information", None))
        self.dynamicTextLabel.setText(QCoreApplication.translate("Dialog", u"Dynamic Text", None))
        self.staticTextLabel.setText(QCoreApplication.translate("Dialog", u"Selected Resource", None))
        self.settingsGroup.setTitle(QCoreApplication.translate("Dialog", u"Settings", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"ResRef:", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Location:", None))
        self.resourceTypeGroup.setTitle(QCoreApplication.translate("Dialog", u"Resource Type", None))
        self.reuseResourceRadio.setText(QCoreApplication.translate("Dialog", u"Reuse Resource", None))
        self.copyResourceRadio.setText(QCoreApplication.translate("Dialog", u"Copy Resource", None))
        self.createResourceRadio.setText(QCoreApplication.translate("Dialog", u"Create Resource", None))
        self.resourceListGroup.setTitle(QCoreApplication.translate("Dialog", u"Resource List", None))
        self.resourceFilter.setPlaceholderText(QCoreApplication.translate("Dialog", u"Search resources...", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside6
