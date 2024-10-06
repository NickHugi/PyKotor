
################################################################################
## Form generated from reading UI file 'insert_instance.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QSize, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QRadioButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
)

from toolset.gui.widgets.renderer.model import ModelRenderer


class Ui_Dialog:
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName("Dialog")
        Dialog.resize(800, 600)
        self.horizontalLayout = QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.leftPanelLayout = QVBoxLayout()
        self.leftPanelLayout.setObjectName("leftPanelLayout")
        self.previewGroup = QGroupBox(Dialog)
        self.previewGroup.setObjectName("previewGroup")
        self.previewLayout = QVBoxLayout(self.previewGroup)
        self.previewLayout.setObjectName("previewLayout")
        self.previewRenderer = ModelRenderer(self.previewGroup)
        self.previewRenderer.setObjectName("previewRenderer")
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
        self.infoGroup.setObjectName("infoGroup")
        self.infoLayout = QVBoxLayout(self.infoGroup)
        self.infoLayout.setObjectName("infoLayout")
        self.dynamicTextLabel = QLabel(self.infoGroup)
        self.dynamicTextLabel.setObjectName("dynamicTextLabel")
        self.dynamicTextLabel.setWordWrap(True)

        self.infoLayout.addWidget(self.dynamicTextLabel)

        self.staticTextLabel = QLabel(self.infoGroup)
        self.staticTextLabel.setObjectName("staticTextLabel")
        self.staticTextLabel.setWordWrap(True)

        self.infoLayout.addWidget(self.staticTextLabel)


        self.leftPanelLayout.addWidget(self.infoGroup)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.leftPanelLayout.addItem(self.verticalSpacer)


        self.horizontalLayout.addLayout(self.leftPanelLayout)

        self.rightPanelLayout = QVBoxLayout()
        self.rightPanelLayout.setObjectName("rightPanelLayout")
        self.settingsGroup = QGroupBox(Dialog)
        self.settingsGroup.setObjectName("settingsGroup")
        self.formLayout = QFormLayout(self.settingsGroup)
        self.formLayout.setObjectName("formLayout")
        self.label = QLabel(self.settingsGroup)
        self.label.setObjectName("label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.resrefEdit = QLineEdit(self.settingsGroup)
        self.resrefEdit.setObjectName("resrefEdit")
        self.resrefEdit.setEnabled(False)
        self.resrefEdit.setMaxLength(16)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.resrefEdit)

        self.label_2 = QLabel(self.settingsGroup)
        self.label_2.setObjectName("label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.locationSelect = QComboBox(self.settingsGroup)
        self.locationSelect.setObjectName("locationSelect")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.locationSelect)


        self.rightPanelLayout.addWidget(self.settingsGroup)

        self.resourceTypeGroup = QGroupBox(Dialog)
        self.resourceTypeGroup.setObjectName("resourceTypeGroup")
        self.horizontalLayout_2 = QHBoxLayout(self.resourceTypeGroup)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.reuseResourceRadio = QRadioButton(self.resourceTypeGroup)
        self.reuseResourceRadio.setObjectName("reuseResourceRadio")
        self.reuseResourceRadio.setChecked(True)

        self.horizontalLayout_2.addWidget(self.reuseResourceRadio)

        self.copyResourceRadio = QRadioButton(self.resourceTypeGroup)
        self.copyResourceRadio.setObjectName("copyResourceRadio")

        self.horizontalLayout_2.addWidget(self.copyResourceRadio)

        self.createResourceRadio = QRadioButton(self.resourceTypeGroup)
        self.createResourceRadio.setObjectName("createResourceRadio")

        self.horizontalLayout_2.addWidget(self.createResourceRadio)


        self.rightPanelLayout.addWidget(self.resourceTypeGroup)

        self.resourceListGroup = QGroupBox(Dialog)
        self.resourceListGroup.setObjectName("resourceListGroup")
        self.verticalLayout_2 = QVBoxLayout(self.resourceListGroup)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.resourceFilter = QLineEdit(self.resourceListGroup)
        self.resourceFilter.setObjectName("resourceFilter")
        self.resourceFilter.setClearButtonEnabled(True)

        self.verticalLayout_2.addWidget(self.resourceFilter)

        self.resourceList = QListWidget(self.resourceListGroup)
        self.resourceList.setObjectName("resourceList")
        self.resourceList.setSortingEnabled(True)
        self.resourceList.setAlternatingRowColors(True)

        self.verticalLayout_2.addWidget(self.resourceList)


        self.rightPanelLayout.addWidget(self.resourceListGroup)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName("buttonBox")
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
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", "Insert Instance", None))
        self.previewGroup.setTitle(QCoreApplication.translate("Dialog", "Preview", None))
        self.infoGroup.setTitle(QCoreApplication.translate("Dialog", "Information", None))
        self.dynamicTextLabel.setText(QCoreApplication.translate("Dialog", "Dynamic Text", None))
        self.staticTextLabel.setText(QCoreApplication.translate("Dialog", "Selected Resource", None))
        self.settingsGroup.setTitle(QCoreApplication.translate("Dialog", "Settings", None))
        self.label.setText(QCoreApplication.translate("Dialog", "ResRef:", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", "Location:", None))
        self.resourceTypeGroup.setTitle(QCoreApplication.translate("Dialog", "Resource Type", None))
        self.reuseResourceRadio.setText(QCoreApplication.translate("Dialog", "Reuse Resource", None))
        self.copyResourceRadio.setText(QCoreApplication.translate("Dialog", "Copy Resource", None))
        self.createResourceRadio.setText(QCoreApplication.translate("Dialog", "Create Resource", None))
        self.resourceListGroup.setTitle(QCoreApplication.translate("Dialog", "Resource List", None))
        self.resourceFilter.setPlaceholderText(QCoreApplication.translate("Dialog", "Search resources...", None))
    # retranslateUi

